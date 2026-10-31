using System;
using Ardleigh.Custom.Common;

namespace Ardleigh.Custom.Misc
{
    public class Proc7 : IServerJob
    {
        private readonly IDbSession _d;

        public Proc7(IDbSession d)
        {
            _d = d;
        }

        public void Run(DateTime t)
        {
            var q = _d.Query("SELECT k1, k2, v FROM zz_tmp_x1 WHERE f = 2");
            foreach (System.Data.DataRow r in q.Rows)
            {
                var n = (int)r["v"] ^ 0x5A;
                if (n % 7 == 3)
                {
                    Svc.Call("U7", r["k1"], r["k2"], n);
                }
            }
        }
    }
}
