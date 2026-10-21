# Methodology & Sources

### An economic framework for prioritizing school food-access outreach in Philadelphia

**Abstract.** This application supports decisions about allocating limited food-access outreach capacity across Philadelphia schools. It combines economic disadvantage, geographic access to listed supermarkets, nearby food-resource availability, and school enrollment in a transparent, weighted index. Its purpose is to identify candidates for further investigation and compare allocation choices under explicit assumptions. It is a descriptive decision-support model, not a causal estimate of program effectiveness, an eligibility determination, or a validated prediction of food insecurity. The weights and cutoffs are planning choices, rather than parameters estimated from observed program outcomes.

## 1. The economic problem: scarcity, access, and opportunity cost

A fixed budget, limited staff time, and delivery capacity make universal service infeasible in a given planning cycle. Choosing one school can mean postponing another. The relevant economic question is therefore not simply “Where is need high?” but “Which feasible allocation best serves the organization's stated objective?”

The app separates two decisions: **measuring priority** using available indicators, and **allocating outreach** given a budget and capacity. A high-need school is not necessarily the school at which an additional dollar produces the largest improvement. The latter requires evidence about treatment effects and school-specific costs that this model does not yet contain.

Access is also broader than the physical presence of food. Sen's entitlement approach emphasizes people's ability to command resources, rather than aggregate availability alone [1]. Applied here, a nearby supermarket is only one aspect of access: prices, income, transport, eligibility, opening hours, and reliability determine whether a family can use it. The app measures a subset of these constraints; it does not operationalize or empirically test Sen's full framework.

## 2. Equity, efficiency, and the choice of objective

An efficiency objective might emphasize potential student reach per outreach cycle. An equity objective might give greater priority to schools facing economic disadvantage or limited nearby resources. These objectives can select different portfolios, even under the same budget. Distributional weights are normative: the literature on inequality measurement makes clear that judgments about the relative importance of disadvantage must be stated explicitly [2].

The Budget & Allocation Lab makes these choices visible through three rules:

- **Need first:** select schools in the current composite-priority order.
- **Student reach first:** select schools with the largest estimated participating enrollment, with scenario score and School ID as tie breakers.
- **Economic disadvantage first:** select schools with the largest enrollment multiplied by the economic-disadvantage proportion, with scenario score and School ID as tie breakers. This targets the estimated *number* of disadvantaged students, not necessarily the highest disadvantage *rate*.

These are alternative planning rules, not estimates of an economically optimal social-welfare policy. The app does not estimate utility, benefits in dollars, willingness to pay, or marginal treatment effects.

## 3. Population, observation unit, and service status

The observation unit is a **school**, identified by School ID. The imported model contains Philadelphia district, charter, and contracted-school records; the targeting pool uses the workbook's stored eligibility flag, whose stated scope is district schools and eligible charters. Contracted records are outside that stated targeting scope. Charter Title I eligibility uses the last populated 2025–26 designation where the current directory omits it and requires confirmation before commitments.

A complete scenario score is required for inclusion in a rankable list. The original “Already served” field is a staff flag: “No” means unchecked, not proof of no historical service. The separately supplied service sheet identifies 15 currently served and 3 formerly served schools. The Served Schools page shows those groups separately.

**Implementation detail that affects interpretation:** Distance review excludes confirmed currently served schools before selecting its top 20. Other existing ranking and budget pages still follow the model's stored eligibility/service flags and can include schools in the separate service list. Staff should reconcile that list before using a portfolio as an expansion commitment. The served-school comparison intentionally retains the existing citywide rank reference.

## 4. Measurement and baseline scoring

The workbook assigns component points before the app loads them. The app imports those points and recalculates the weighted sum; it does not rebuild the underlying source joins, eligibility decisions, or scoring bands on every request.

| Component | Maximum baseline points | Workbook scoring bands | Economic interpretation |
| --- | ---: | --- | --- |
| Economic disadvantage | 30 | ≥90%: 30; ≥80%: 25; ≥70%: 20; ≥60%: 15; ≥50%: 10; ≥40%: 5; <40%: 0 | A proxy for household economic constraint at school level |
| Fresh-food access distance | 25 | >1 mile: 25; 0.75–1: 20; 0.50–<0.75: 15; 0.25–<0.50: 10; <0.25: 5 | Greater distance to the nearest listed qualifying supermarket increases priority |
| Nearby resource gap | 25 | 0 resources: 25; 1: 20; 2: 15; 3: 10; 4: 5; ≥5: 0 | Fewer listed resources within one mile increase priority |
| Potential reach / enrollment | 5 | ≥700 students: 5; 500–699: 4; 350–499: 3; 200–349: 2; <200: 1 | A limited contribution for the scale of possible outreach |

Counts of resources do not measure the amount, nutritional quality, affordability, or reliability of food available. Enrollment is not observed participation. A school-level disadvantage rate cannot establish the circumstances of every enrolled student: doing so would be an ecological inference error.

## 5. Composite index and scenario weights

Let pᵢₖ be the imported points for school i on component k, and Mₖ its baseline maximum: 30, 25, 25, and 5. Let rₖ ≥ 0 be the user's slider values. The app normalizes the slider values to weights wₖ that sum to 85:

$$w_k = 85\frac{r_k}{\sum_j r_j},\qquad S_i = \sum_k w_k\frac{p_{ik}}{M_k}.$$

If all sliders are zero, the app restores baseline weights (30, 25, 25, 5). At baseline, the score equals the sum of the imported component points. A complete score requires all four component-point fields; the app does not impute missing component points.

This is an **additive multi-criteria index**. It is transparent but compensatory: a higher score on one dimension can offset a lower score on another. Indicators can also overlap conceptually—for example, income constraints and geographic disadvantage may be correlated—so component weights should not be interpreted as independent causal contributions. OECD/JRC guidance on composite indicators emphasizes the importance of transparent weighting, aggregation, and sensitivity analysis [3].

The same numeric tier cutoffs are applied to scenario scores: Tier 1 ≥70; Tier 2 ≥55 and <70; Tier 3 ≥40 and <55; Tier 4 <40. These are planning categories, not empirically calibrated thresholds of food insecurity. Keeping an 85-point scale does **not** make different weight choices substantively equivalent. A tier change may reflect a changed value judgment rather than a change in local conditions.

## 6. Ranking, filters, and interpretation of order

Schools are sorted by scenario score descending, economic-disadvantage proportion descending, enrollment descending, then School ID ascending. Equal scores share a minimum rank; the sequential **Order** field distinguishes their display positions using the tie breakers. School IDs are stored as text for sorting.

Overview applies school-type and grade-level filters **before** selecting the top 15. Distance review excludes currently served schools, applies its type/level filters, then selects the top 20. If fewer eligible schools match, the app shows the smaller group. Combined grade levels remain separate source categories. The displayed citywide scenario ranks are not renumbered within each filtered group.

Scenario Lab compares changes in rank under different weights. It is a sensitivity exercise, not a statistical confidence interval. A fuller robustness analysis would vary weights systematically, examine alternative indicator definitions and missing-data treatments, and report how often a school remains in the top group. Such a simulation is a proposed extension, not a result currently produced by the app.

## 7. Geography and food-resource evidence

Fresh access uses the nearest USDA-listed SNAP supermarket/superstore in the imported source. Nearby resource counts use distinct active City Food Site addresses within one straight-line mile, excluding recorded closure flags. Smaller retailers, food quality, prices, walking barriers, and distribution capacity are not adequately represented by these indicators.

The detailed school food-site tables come from the supplied October 20 workbook: 309 site records were extracted, and the app shows only active candidate listings within one mile of the selected school after excluding recorded closures. It recomputes distances for each school rather than reusing distances cached for the workbook's selected school. Multiple listings may share an address; their number need not equal the distinct-address resource count. Website links identify listed providers or networks and do not demonstrate current service availability.

Distances use the Haversine formula with Earth radius 3958.7613 miles. They measure geographic separation, not road distance, route duration, or a school's catchment area. Distance review highlights close pairs as prompts for staff investigation; proximity alone does not establish duplicated participants or benefits. Share's dispatch address is 2901 W. Hunting Park Avenue, Philadelphia. Its default map coordinates are approximate and editable because live geocoding was unavailable; hub distances inherit that location uncertainty.

Research on nutritional inequality finds that geographic retail access alone does not explain all differences in food purchasing [4]. That motivates treating the app's distance measures as partial proxies, not claiming that adding a nearby site will necessarily improve diets or food security. The cited research does not validate this app's weights or thresholds.

## 8. Budget allocation and opportunity cost

Let B be the available budget, c > 0 the assumed cost per school for one outreach cycle, C the school-capacity limit, and N the number of candidate schools. Each strategy can select:

$$K = \min\left(\lfloor B/c\rfloor, C, N\right).$$

With common assumed student participation p, estimated reach at school i is pEᵢ, where Eᵢ is enrollment. The lab selects K schools under each rule, calculates estimated spend Kc and remaining funds B − Kc, and compares estimated participation. Under equal school costs and a common participation rate, selecting the largest pEᵢ values maximizes total estimated reach. This conclusion would not generally hold with heterogeneous costs, capacity, or participation rates.

The displayed **reach opportunity cost** is the reach-first total minus the total under the selected strategy. It is a difference in modeled potential participation, not lost welfare, lost actual beneficiaries, or forgone causal benefit. School-specific delivery costs, geographic routing, fixed startup costs, repeat-service needs, and overlapping enrollment are not modeled. Budget and participation defaults are illustrative assumptions, not observed estimates.

A future benefit-focused allocation could maximize expected incremental outcomes under a budget. That would require credible estimates of each intervention's benefits and costs; replacing an unknown effect with the current need score would not solve the problem.

## 9. Measuring outcomes and learning about benefit

The outcome log separates **inputs** (actual cost), **outputs** (students served), and an **outcome indicator** (food insecurity before and after among paired respondents). Users must apply the same question, definition, population, and follow-up period across schools. The app does not currently administer a validated food-security questionnaire.

Observed cost per student uses only schools with both cost and students-served entries. The food-insecurity change uses only schools with complete paired-response counts and before/after totals. The reduction in percentage points is 100 × (total before − total after) / total paired responses, so schools are weighted by response counts rather than equally. Missing entries are not filled with zero; there is no meaningful rate when the denominator is zero. Counts are aggregate and school-level; cross-school duplication may remain.

A before–after improvement is **not by itself a causal effect**. Selection into outreach, changing economic conditions, seasonality, other programs, nonresponse, and regression to the mean can all affect observed changes. The causal question concerns what would have happened to the same population without the intervention—the counterfactual [5].

For stronger evidence, consider a feasible, ethically reviewed phased rollout or a carefully chosen comparison group. A difference-in-differences design would compare changes in treated and comparison groups, but requires a defensible parallel-trends assumption and attention to spillovers and composition changes. A randomized rollout requires a genuinely random assignment process, a defined outcome and follow-up period, and analysis consistent with the assignment unit. Neither design is currently implemented by this app.

Outcome records last only for the current session unless downloaded and later reuploaded. They are not a persistent evaluation database. Do not enter student names or individual records into the aggregate log.

## 10. Data provenance, refresh, and reproducibility

- **Core school-model snapshot:** October 9, 2026. Directory information is for 2026–27; enrollment/demographic inputs use 2025–26 published files. Reporting periods differ from retrieval dates.
- **School directory and enrollment:** School District of Philadelphia public data. Economic-disadvantage inputs come from Pennsylvania Department of Education low-income reporting. Source definitions may differ from a household food-insecurity measure.
- **Detailed food listings:** extracted from `SBD_Expansion_Model_10.20.2026.xlsx`, supplied October 20, 2026; the workbook reports government-source retrieval on October 9. These are frozen observations, not live API queries each time a page opens.
- **Service status:** a separate SY26–27 master sheet supplied October 14, 2026. Only the school-ID crosswalk and service grouping were published; staff contacts and internal notes were omitted. Three rows explicitly listed as no longer served are kept separate from current service.
- **Verified overrides:** the workbook describes dated staff evidence and a 180-day validity rule. The app imports the saved effective values and validity fields; it does not automatically revisit the original workbook or re-evaluate override expiry against today's date.
- **Refresh process:** source retrieval, school-key validation, scoring, and review reconciliation must occur before regenerating the CSV snapshots. Opening or rebooting the app does not refresh the underlying datasets.

A reproducible planning record should retain the data snapshot, service-list version, selected filters, scenario weights, budget assumptions, and any edited hub coordinates. Existing exports capture some of these fields but do not constitute a complete versioned audit record. Before operational commitments, verify eligibility and service status, inspect missing inputs, confirm provider availability, and assess whether the source definitions suit the intended decision.

## 11. Limitations and appropriate use

The app is appropriate for screening, generating an outreach shortlist, explaining tradeoffs, and designing data collection. It should not be used to claim precise household need, assign automatic program eligibility, infer causal impact, or optimize delivery routes. Discrete scoring bands introduce jumps around cutoffs; the model provides neither uncertainty intervals nor out-of-sample validation. Results depend on the candidate scope, data completeness, proxy definitions, weights, and staff reconciliation of service status.

The strongest next development is to link planning decisions to credible outcome evidence: measure participation, actual cost, and comparable food-security outcomes, then evaluate which interventions produce additional benefit. This would make it possible to move from **prioritizing apparent need** toward **allocating resources using evidence of incremental impact**.

## References

[1] Sen, A. (1981). *Poverty and Famines: An Essay on Entitlement and Deprivation*. Oxford University Press. Conceptual foundation for distinguishing food availability from the ability to access food.

[2] Atkinson, A. B. (1970). On the measurement of inequality. *Journal of Economic Theory, 2*(3), 244–263. [doi:10.1016/0022-0531(70)90039-6](https://doi.org/10.1016/0022-0531(70)90039-6). Foundation for making distributional value judgments explicit; not a calibration of this model's equity weights.

[3] OECD & European Commission, Joint Research Centre. (2008). *Handbook on Constructing Composite Indicators: Methodology and User Guide*. OECD Publishing. [doi:10.1787/9789264043466-en](https://doi.org/10.1787/9789264043466-en). Guidance on index construction, weighting, aggregation, and robustness.

[4] Allcott, H., Diamond, R., Dubé, J.-P., Handbury, J., Rahkovsky, I., & Schnell, M. (2019). Food deserts and the causes of nutritional inequality. *The Quarterly Journal of Economics, 134*(4), 1793–1844. [doi:10.1093/qje/qjz015](https://doi.org/10.1093/qje/qjz015). Empirical context for the limits of geographic-access explanations; not an evaluation of this program.

[5] Angrist, J. D., & Pischke, J.-S. (2009). *Mostly Harmless Econometrics: An Empiricist's Companion*. Princeton University Press. [doi:10.1515/9781400829828](https://doi.org/10.1515/9781400829828). Background on causal identification, experiments, and quasi-experimental methods.
