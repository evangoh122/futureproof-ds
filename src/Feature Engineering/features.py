# Derived features the model reads, built on top of the silver layer.
def add_features(data):
    data = data.copy()
    data["sessions_3d"] = data[["sessions_day1", "sessions_day2", "sessions_day3"]].sum(axis=1)
    data["active_days_3d"] = (data[["sessions_day1", "sessions_day2", "sessions_day3"]] > 0).sum(axis=1)
    data["day1_share"] = data["sessions_day1"] / data["sessions_3d"]
    data["listen_share"] = data["listen_sessions_3d"] / data["sessions_3d"]
    data["avg_session_minutes"] = data["total_minutes_3d"] / data["sessions_3d"]

    # Trials with no sessions in the first 3 days divide by zero above. Zero
    # engagement is real information, so those become zeros rather than NaN.
    for col in ["day1_share", "listen_share", "avg_session_minutes"]:
        data[col] = data[col].fillna(0)

    return data
