Fairness Benchmarking: Test bias mitigation algorithms on ad
recommendation. For instance, build two job recommendation models – one
standard and one bias-corrected – and use this data to compare how evenly
they distribute opportunities across the proxy gender groups.
Ad Audience Analysis: Analyze the user features to see if certain groups
(e.g., proxy-female vs proxy-male) were less likely to be shown certain job
ads. This can highlight unintentional biases in targeting.
Custom Fairness Metric: Develop a new metric or visualization for
“opportunity parity”
– ensuring that qualified candidates have equal chance to
see relevant jobs. Use the dataset’s structure (inbound user requests vs.
outbound ad shown) to compute this.
Algorithmic Experimentation: Implement techniques like adversarial
debiasing or fairness-constrained optimization on recommendation
algorithms, and use FairJob data to demonstrate how these techniques
improve equity with minimal loss in accuracy