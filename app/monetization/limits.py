from app.monetization.plans import Plan


PLAN_LIMITS = {
    Plan.FREE: {
        "daily_runs": 3,
        "scheduled_queries": 1,
    },
    Plan.PRO: {
        "daily_runs": 20,
        "scheduled_queries": 3,
    },
    Plan.ENTERPRISE: {
        "daily_runs": 1000,
        "scheduled_queries": 10,
    },
}
