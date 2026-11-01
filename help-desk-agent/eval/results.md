# Evaluation Results

Mode: offline scripted model
Result: 13/13 passed

The offline mode exercises tool execution, deterministic calculations, and answer checks; it does not measure LLM quality. Use `python eval/run_eval.py --live` to evaluate Gemini tool selection and responses.

| Question | Result | Details |
| --- | --- | --- |
| hours-saturday | PASS | All checks passed |
| ebike-day-price | PASS | All checks passed |
| age-limit-ebike | PASS | All checks passed |
| location | PASS | All checks passed |
| refund-50-percent | PASS | All checks passed |
| refund-100-percent | PASS | All checks passed |
| refund-under-24-hours | PASS | All checks passed |
| voucher-refund | PASS | All checks passed |
| unknown-booking | PASS | All checks passed |
| unrelated-question | PASS | All checks passed |
| unsupported-service | PASS | All checks passed |
| dogs | PASS | All checks passed |
| bike-abroad | PASS | All checks passed |
