# Analytical Framework

How the app moves from school data to outreach decisions.

### 1. Measure need

Four indicators capture economic disadvantage, distance to listed fresh food, the nearby resource gap, and potential student reach. Their baseline maximum points are **30, 25, 25, and 5**. These are transparent planning choices, not estimated treatment effects.

### 2. Calculate priority

For school i, let pᵢₖ be its imported points and Mₖ the maximum for component k. User-selected weight values rₖ become weights that total 85:

$$
w_k = 85\frac{r_k}{\sum_j r_j}, \qquad S_i = \sum_k w_k\frac{p_{ik}}{M_k}
$$

Blank weight fields use their baseline values; all-zero entries restore baseline weights. A missing component prevents a complete score. Schools sort by score, economic disadvantage, enrollment, then School ID. Filters apply before selecting the Overview's top 15 or Distance review's top 20; Distance review also applies its Served Schools filter before selecting the top 20. Blank filters leave the pool unrestricted.

### 3. Allocate scarce resources

For budget B, equal cost per school c, capacity C, and N candidates:

$$
K = \min\left(\lfloor B/c\rfloor, C, N\right), \qquad \widehat{R}_i = pE_i
$$

K is the number of schools affordable within capacity. Estimated reach is enrollment Eᵢ times assumed participation p. The Budget Lab compares need-first, reach-first, and disadvantaged-enrollment allocations. Its opportunity cost is the estimated reach forgone relative to reach-first—not lost proven benefit.

### 4. Learn from outcomes

The outcome log records actual costs, students served, and paired food-insecurity counts:

$$
\text{Observed reduction (percentage points)} = 100\frac{\text{Before count} - \text{After count}}{\text{Paired responses}}
$$

Complete paired records are pooled; a zero denominator gives no rate. Before–after change alone does not establish causation. A credible comparison group or randomized phased rollout would strengthen evidence.

**Economic interpretation:** scarcity creates opportunity costs; equity and reach can favor different schools. Need scores guide investigation, while evidence about incremental benefit should guide future refinement. Listed food access and straight-line distances remain partial proxies.

### Further reading

- OECD/JRC (2008), *Handbook on Constructing Composite Indicators*: [weights and index design](https://doi.org/10.1787/9789264043466-en).
- Allcott et al. (2019), *Food Deserts and the Causes of Nutritional Inequality*: [limits of geographic access alone](https://doi.org/10.1093/qje/qjz015).
- Angrist & Pischke (2009), *Mostly Harmless Econometrics*: [causal evaluation](https://doi.org/10.1515/9781400829828).
