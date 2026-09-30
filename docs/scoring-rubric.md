# Fleet-study scoring rubric

The scorer reads only the frozen dataset references and the raw prediction tape. A raw record is
either `ok` with an observed output or a preserved failure/abstention; failures never become a
correct or incorrect answer.

Task domains use exact reference comparison for passage and executable cases. Adversarial cases
are scored against the frozen expected action and separately counted as false accepts. Qualitative
style cases are unscored until an anonymized independent rating sheet is supplied; no quality
claim is made from model self-report or keyword matches.

Accuracy and coverage retain their denominators. Zero scored rows produce undefined accuracy
(`null`) and an `inconclusive` decision. Bootstrap intervals resample source-family clusters with
the fixed scoring seed 17, so repeated rows within a family cannot masquerade as independent
observations. Calibration columns are emitted only for records carrying numeric confidence.

Artifact validity, experiment result, and routing eligibility are distinct. A valid negative or
inconclusive bundle is publishable as evidence but is not eligible to serve.
