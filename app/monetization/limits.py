from app.monetization.plans import Plan


PLAN_LIMITS = {
    Plan.FREE: {
        "daily_runs": 3,
    },
    Plan.PRO: {
        "daily_runs": 20,
    },
    Plan.ENTERPRISE: {
        "daily_runs": 1000,
    },
}
