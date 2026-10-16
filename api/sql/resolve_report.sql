-- Publication date determines the latest report; identifiers resolve ties.
SELECT report_id FROM reports
ORDER BY publication_date DESC, report_id DESC LIMIT 1
