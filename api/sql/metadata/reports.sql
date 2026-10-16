-- Newest publication first; report identifiers resolve ties.
SELECT report_id, publication_date FROM reports
ORDER BY publication_date DESC, report_id DESC
