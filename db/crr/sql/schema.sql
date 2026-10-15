PRAGMA foreign_keys = ON;

CREATE TABLE reports (
    report_id INTEGER PRIMARY KEY,
    publication_date TEXT NOT NULL
);

CREATE TABLE account_holders (
    account_holder TEXT PRIMARY KEY,
    legal_name TEXT,
    email_domain TEXT
);

CREATE TABLE settlement_points (
    settlement_point TEXT PRIMARY KEY,
    longitude REAL,
    latitude REAL,
    point_type TEXT,
    load_zone TEXT,
    capacity_mw REAL
);

CREATE TABLE tou_hours (
    delivery_month TEXT NOT NULL,
    time_of_use TEXT NOT NULL,
    hours INTEGER NOT NULL,
    PRIMARY KEY (delivery_month, time_of_use)
);

CREATE TABLE crr_holdings (
    report_id INTEGER NOT NULL REFERENCES reports,
    crr_id INTEGER NOT NULL,
    segment_id INTEGER NOT NULL,
    account_holder TEXT NOT NULL REFERENCES account_holders,
    hedge_type TEXT NOT NULL,
    crr_type TEXT NOT NULL,
    source TEXT NOT NULL REFERENCES settlement_points,
    sink TEXT NOT NULL REFERENCES settlement_points,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    time_of_use TEXT NOT NULL,
    mw REAL NOT NULL,
    PRIMARY KEY (report_id, crr_id, segment_id)
);

CREATE TABLE crr_monthly_holdings (
    report_id INTEGER NOT NULL REFERENCES reports,
    account_holder TEXT NOT NULL REFERENCES account_holders,
    source TEXT NOT NULL REFERENCES settlement_points,
    sink TEXT NOT NULL REFERENCES settlement_points,
    delivery_month TEXT NOT NULL,
    hedge_type TEXT NOT NULL,
    peak_wd_mw REAL NOT NULL,
    peak_we_mw REAL NOT NULL,
    off_peak_mw REAL NOT NULL,
    peak_wd_mwh REAL NOT NULL,
    peak_we_mwh REAL NOT NULL,
    off_peak_mwh REAL NOT NULL,
    PRIMARY KEY (report_id, account_holder, source, sink, delivery_month, hedge_type)
);

CREATE TABLE crr_summary_holdings (
    report_id INTEGER NOT NULL REFERENCES reports,
    account_holder TEXT NOT NULL REFERENCES account_holders,
    source TEXT NOT NULL REFERENCES settlement_points,
    sink TEXT NOT NULL REFERENCES settlement_points,
    hedge_type TEXT NOT NULL,
    mwh REAL NOT NULL,
    PRIMARY KEY (report_id, account_holder, source, sink, hedge_type)
);
