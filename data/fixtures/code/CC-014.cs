// BILLADJ_NIGHTLY
// Installed 2017. Changed 2019, 2021 (CR move), 2023.
using System;
using System.Data;
using Ardleigh.Custom.Common;

namespace Ardleigh.Custom.Billing
{
    public class BillingAdjustmentJob : IServerJob
    {
        private const decimal Limit = 0.10m;
        private const string ApprovalPending = "P";
        private const string ApprovalCleared = "A";

        private readonly IDbSession _db;
        private readonly IJobLog _log;

        public BillingAdjustmentJob(IDbSession db, IJobLog log)
        {
            _db = db;
            _log = log;
        }

        public void Run(DateTime runDate)
        {
            var lines = _db.Query(@"
                SELECT w.project_id, w.billing_line_id, w.adjust_type, w.adjust_value,
                       l.billable_value, p.partner_code, r.override_rate
                FROM   zz_billing_adjust_queue w
                JOIN   billing_line l ON l.billing_line_id = w.billing_line_id
                JOIN   project p ON p.project_id = w.project_id
                LEFT JOIN zz_rate_override r ON r.client_id = p.client_id
                                            AND r.grade_code = l.grade_code
                WHERE  w.processed = 0 AND w.queue_date <= @runDate",
                new { runDate });

            foreach (DataRow line in lines.Rows)
            {
                var billable = (decimal)line["billable_value"];
                var value = (decimal)line["adjust_value"];

                if (line["override_rate"] != DBNull.Value)
                {
                    billable = Reprice(line, (decimal)line["override_rate"]);
                }

                if ((string)line["adjust_type"] == "D" && Needs(billable, value))
                {
                    if (!Cleared((long)line["billing_line_id"]))
                    {
                        Hold(line, runDate);
                        continue;
                    }
                }

                Apply(line, billable, value, runDate);
            }
        }

        private static bool Needs(decimal billable, decimal value)
        {
            return billable != 0m && Math.Abs(value) / billable > Limit;
        }

        private bool Cleared(long lineId)
        {
            var status = _db.Scalar<string>(
                "SELECT status FROM zz_writedown_approval WHERE billing_line_id = @lineId",
                new { lineId });
            return status == ApprovalCleared;
        }

        private void Hold(DataRow line, DateTime runDate)
        {
            _db.Execute(@"
                INSERT INTO zz_writedown_approval
                    (billing_line_id, project_id, partner_code, status, requested_on)
                SELECT @lineId, @projectId, @partner, @status, @runDate
                WHERE NOT EXISTS (SELECT 1 FROM zz_writedown_approval
                                  WHERE billing_line_id = @lineId)",
                new
                {
                    lineId = (long)line["billing_line_id"],
                    projectId = (string)line["project_id"],
                    partner = (string)line["partner_code"],
                    status = ApprovalPending,
                    runDate,
                });
        }

        private void Apply(DataRow line, decimal billable, decimal value, DateTime runDate)
        {
            var sign = (string)line["adjust_type"] == "D" ? -1m : 1m;

            _db.Execute(@"
                UPDATE billing_line
                SET    billable_value = @newValue, adjusted_on = @runDate, adjusted_by = 'BILLADJ'
                WHERE  billing_line_id = @lineId",
                new
                {
                    newValue = billable + sign * value,
                    runDate,
                    lineId = (long)line["billing_line_id"],
                });

            _db.Execute(@"
                UPDATE zz_billing_adjust_queue SET processed = 1, processed_on = @runDate
                WHERE  billing_line_id = @lineId",
                new { runDate, lineId = (long)line["billing_line_id"] });

            _log.Info($"Adjusted line {line["billing_line_id"]}");
        }

        private static decimal Reprice(DataRow line, decimal rate)
        {
            var hours = (decimal)line["billable_value"] / StandardRates.For(line);
            return Math.Round(hours * rate, 2, MidpointRounding.AwayFromZero);
        }
    }
}
