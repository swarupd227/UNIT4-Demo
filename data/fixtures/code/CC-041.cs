// TSLOCK_WEEKLY
// Stamps submitted timesheets as locked once the period is closed.
// Owner: Finance systems. Spec: FS-TS-012.
using System;
using Ardleigh.Custom.Common;

namespace Ardleigh.Custom.Time
{
    public class TimesheetLockJob : IServerJob
    {
        private readonly IDbSession _db;

        public TimesheetLockJob(IDbSession db)
        {
            _db = db;
        }

        public void Run(DateTime runDate)
        {
            var closedTo = _db.Scalar<DateTime>(
                "SELECT MAX(period_end) FROM time_period WHERE status = 'C'");

            _db.Execute(@"
                UPDATE timesheet_line
                SET    locked = 1, locked_on = @runDate
                WHERE  work_date <= @closedTo AND locked = 0",
                new { runDate, closedTo });
        }
    }
}
