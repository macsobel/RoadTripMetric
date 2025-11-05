# A Standardized Metric for Electric Vehicle Road Trip Performance Using Dynamic Programming

**Aaron Sobel¹** and **Jarrod Brown¹**

¹U.S. Environmental Protection Agency, Office of Transportation and Air Quality, Ann Arbor, MI 48105, USA

**Corresponding author**: Aaron Sobel (sobel.aaron@epa.gov)

---

## Abstract

Comparing electric vehicles for long-distance travel remains challenging because performance depends on the complex interaction between vehicle range, energy efficiency, and charging speed. Unlike fuel economy ratings for gasoline vehicles, no standardized metric exists for electric vehicle road trip capability. This study develops a dynamic programming algorithm that optimizes charging strategy to minimize total travel time on a standardized 1,000-mile highway trip. Using empirical charging data from the Electric Vehicle Knowledge Exchange database, we demonstrate the approach with a Volkswagen ID.4 case study, showing optimal strategies that differ substantially from typical driver behavior. The algorithm identifies that charging to only 53 percent rather than the conventional 80 percent minimizes trip time to 14.83 hours. This metric provides consumers and policymakers with a simple, analogous comparison tool for evaluating electric vehicle long-distance performance.

**Keywords:** Electric vehicles; dynamic programming; charging optimization; travel time; battery management; transportation energy

---

## Highlights

- Dynamic programming algorithm optimizes EV charging strategy for 1,000-mile trips
- Standardized metric enables direct comparison of electric vehicle road trip capability  
- Optimal charging to 53% significantly faster than conventional 80% charging behavior
- Algorithm completes in under one second enabling interactive vehicle comparison
- Case study demonstrates 14.83-hour trip time for Volkswagen ID.4 under standard conditions

---

## 1. Introduction

### 1.1 Background

Ask someone shopping for an electric vehicle about their biggest concern, and "road trips" often tops the list. The worry is understandable. With gasoline cars, refueling takes 5 minutes regardless of the model you choose. With electric vehicles, it is complicated. A 1,000-mile trip might take vastly different amounts of time depending on which vehicle you buy, even if their advertised ranges seem similar.

The problem is that three different factors determine electric vehicle road trip performance: how far you can drive on a full charge (range), how much energy the vehicle consumes per mile (efficiency), and how quickly the battery accepts charge at different charge levels (charging speed). Here is what makes this tricky: these factors interact. A vehicle with 300 miles of range but slow charging might actually be worse for road trips than one with 250 miles of range but very fast charging. 

Currently, manufacturers report these specs separately. You will see "EPA range: 275 miles," "efficiency: 2.8 mi/kWh," and "peak charging: 135 kW" on spec sheets. But what does this mean for your actual road trip? Most buyers cannot easily translate these numbers into "how long will it take me to drive from Seattle to San Francisco?"

### 1.2 Research Gap and Objectives

Tools like A Better Route Planner (ABRP) have become indispensable for electric vehicle owners planning specific routes. Tell ABRP you are driving from Denver to Salt Lake City, and it will tell you exactly where to stop, how long to charge, and when you will arrive. These tools are excellent for trip planning but less useful for comparing vehicles. 

The issue is that ABRP's answer depends entirely on the route. That same vehicle might perform very differently on a flat interstate versus a mountainous backroad, or in summer versus winter. So if you are shopping for an electric vehicle and want to know which model is genuinely better for long trips in general, you are stuck. You could run dozens of hypothetical routes through ABRP for each vehicle you are considering, but who has time for that? Most people fall back on crude proxies—"this one has more range, so it must be better"—which often leads to wrong conclusions.

### 1.3 Contribution and Organization

We developed a standardized metric for comparing electric vehicles: how long does it take to drive 1,000 miles under controlled conditions? Pick a fixed highway speed (70 mph), assume chargers every 50 miles, start with a full battery, and optimize the charging strategy. The result is a single number—say, 14.8 hours—that naturally incorporates range, efficiency, and charging speed.

The technical challenge is finding the optimal charging strategy. Should you charge to 80 percent at each stop? Or make more frequent stops but charge to only 50 percent each time? Because charging power drops dramatically at high battery levels (a quirk of lithium-ion chemistry), the answer is not obvious. We use dynamic programming to find the truly optimal solution—the strategy that minimizes total trip time.

We have implemented three variants: one that purely minimizes time, one that uses the fewest possible stops (then minimizes time within that constraint), and one that mimics how people typically charge (staying between 20 and 80 percent battery). We also built a web-based calculator so anyone can run these analyses.

The remainder of this paper is organized as follows: Section 2 reviews existing literature on EV routing and charging optimization. Section 3 presents the problem formulation and dynamic programming methodology. Section 4 describes the data sources and implementation details. Section 5 presents results from a VW ID.4 case study. Section 6 discusses implications and limitations, and Section 7 concludes.

---

## 2. Literature Review

### 2.1 EV Routing and Range Anxiety

Electric vehicle adoption faces significant barriers related to long-distance travel capability. Neubauer and Wood (2014) demonstrate that range anxiety substantially impacts perceived EV utility, even when actual daily driving patterns would accommodate most battery electric vehicles. This psychological barrier stems from the complex interaction between vehicle range, charging infrastructure availability, and trip planning requirements.

Traditional route optimization methods for internal combustion vehicles focus primarily on distance or time minimization, with refueling treated as a negligible constraint. Electric vehicles fundamentally alter this paradigm, requiring explicit modeling of energy consumption, charging infrastructure, and time-dependent charging dynamics (Pelletier et al., 2016).

### 2.2 Charging Optimization Approaches

Recent research has addressed EV routing through various optimization frameworks. Yang and Sun (2015) formulate the battery swap station location-routing problem, though battery swapping has seen limited commercial adoption. Yi and Bauer (2017) develop stochastic eco-routing solutions that minimize energy consumption, but do not explicitly optimize charging stop locations or durations.

Zhang et al. (2017) present multi-day scenario analysis for charging infrastructure planning, demonstrating the importance of considering realistic charging behavior. However, their approach focuses on infrastructure placement rather than vehicle comparison metrics. Similarly, Wolbertus et al. (2016) benchmark charging infrastructure utilization patterns but do not address optimal charging strategies for individual vehicles.

Dynamic programming has been successfully applied to related vehicle routing problems. Brooker et al. (2015) use DP methods in the FASTSim vehicle simulation tool, though focused on drive cycle analysis rather than charging optimization. The gap in existing literature is a standardized, computationally efficient method for comparing vehicles across controlled long-distance scenarios.

### 2.3 Consumer Information and Decision Tools

Current consumer-facing tools like A Better Route Planner (ABRP, 2024) provide route-specific planning but cannot produce standardized vehicle comparison metrics. Nicholas and Hall (2018) document lessons from early fast-charging deployments, noting the critical need for better consumer information about vehicle charging performance. The Electric Vehicle Knowledge Exchange (EVKX, 2024) has emerged as a community-driven source for empirical charging data, addressing the lack of standardized manufacturer reporting.

This study addresses the identified gap by developing a standardized metric using dynamic programming to optimize charging strategy under controlled conditions, enabling direct vehicle-to-vehicle comparison for long-distance travel performance.

---

## 3. Methodology

### 3.1 Problem Formulation

#### 3.1.1 Problem Definition

We model the trip as a straight line: you start at mile 0 and need to reach mile $D$ (for example, 1,000 miles). Fast chargers sit at regular intervals every $s$ miles along the route. Your vehicle starts with a full battery and must arrive with at least 10 percent charge remaining (a safety buffer).

Each vehicle is characterized by its range $R$ at 70 mph and its charging curve $P(\text{SoC})$—how many kilowatts of power flow into the battery at each charge level. This charging curve is where things get interesting. Most electric vehicles charge very fast when the battery is low—often more than 100 kW—but power drops off significantly above 80 percent. From 80 to 100 percent, you might be crawling along at 20 to 30 kW. This makes "always charge to full" a terrible strategy for road trips, even though it feels intuitive.

#### 3.1.2 Constraints

The optimization problem operates under four key constraints. First, state of charge must remain within operational bounds at all times: $\text{SoC}_{\text{min}} \leq \text{SoC}(t) \leq 100$ percent. Second, the vehicle must arrive at the destination with sufficient reserve: $\text{SoC}(D) \geq \text{SoC}_{\text{end}}$. Third, the vehicle must maintain sufficient charge to reach the next charging decision point along the route. Fourth, charging sessions must respect physical battery limitations, operating only between $\text{SoC}_{\text{min}}$ and 100 percent capacity.

#### 3.1.3 Objective Functions

We implement three optimization strategies:

**Strategy 1: Pure Time Minimization**

Find the charging strategy that gets you there fastest, period. Stop anywhere, charge to any level—whatever minimizes total time. This is what we focus on primarily.

**Strategy 2: Minimize Stops First, Then Time**

Some drivers hate stopping frequently, even if each stop is shorter. This strategy first figures out the absolute minimum number of stops needed to complete the trip, then finds the fastest route using exactly that many stops. It's a two-stage process: count the minimum stops (using a greedy simulation), then optimize time with that constraint.

**Strategy 3: Conventional Behavior**

Real drivers don't always optimize perfectly. Many prefer to charge when they're between 20-80% battery—letting it get too low feels risky, and charging past 80% feels slow. This strategy mimics that behavior by only allowing charging sessions to start when you're within a specified range.

#### 3.1.4 Travel Time Components

Total trip time comprises three components. Driving time equals distance divided by constant highway speed (e.g., 200 miles at 70 mph yields 2.86 hours). Charging time calculation proves more complex due to state-dependent charging power. Rather than integrating over continuous power curves, we employ lookup tables containing empirical cumulative charging times from 0 to 100 percent state of charge. To determine charging duration from any initial to target state of charge, we subtract the corresponding cumulative time values and apply linear interpolation between measured data points. Detour time accounts for the overhead of exiting the highway, locating the charger, connecting and disconnecting, and returning to the route. We model this as approximately one mile of additional travel at the average highway speed, capturing the temporal cost of each charging stop.

### 3.2 Dynamic Programming Algorithm

#### 3.2.1 State Space Definition

The key insight is that this problem has "optimal substructure"—a computer science term meaning that the best decision from any point depends only on where you are and how much battery you have, not on how you got there. This makes dynamic programming applicable.

We describe each state by two numbers: your position along the route (in miles) and your current battery percentage. We discretize both: charger locations every 50 miles give us our position states, and we break battery levels into 0.5 percent increments (so 10.0, 10.5, 11.0 percent, and so on). That 0.5 percent resolution is fine enough to be accurate but coarse enough that the computation finishes in less than a second.

At any state, the decision maker faces two options: drive directly to the destination if sufficient battery remains, or stop at one of the upcoming chargers, charge to some target level, then continue optimally from that new state. The algorithm determines which choice minimizes total remaining travel time.

#### 3.2.2 Optimization Logic

Here is how the time-minimization algorithm thinks. Imagine you are at mile 400 with 55 percent battery. The algorithm asks: "What is the fastest way to finish from here?"

**Option 1: Drive to the end.** Do you have enough juice to make it 600 more miles and arrive with 10 percent battery? If the answer is no, skip this option. If yes, calculate the drive time—that is one candidate answer.

**Option 2: Stop at a charger.** Look at each charger you can reach (maybe miles 450, 500, 550, and 600). For each one:
- Calculate how much battery you would have when you arrive
- Try charging to every possible target level (say, from your arrival SoC up to 100 percent, in 0.5 percent steps)
- For each target: add up (drive time to charger plus charging time plus already-calculated best time from that charger at the new battery level)
- Keep track of the option with the lowest total

Battery consumption is proportional to distance. If your vehicle goes 239 miles on a full battery, then 50 miles burns (50 ÷ 239) × 100 = 20.9 percent of your battery.

The algorithm works backward from the destination. At the finish line, if you have at least 10 percent battery, you need zero more time. If you do not, that state is "impossible" (mathematically represented as infinite time).

#### 3.2.3 Backward Induction Process

The algorithm works backward from the end—a technique called backward induction. It's counterintuitive at first but makes sense once you see why.

**Setup**
We lay out chargers every 50 miles and slice battery levels into 0.5 percent chunks. This creates a big table with one entry for each (position, battery level) combination. Initially, all entries are blank.

**Start at the Destination**
The destination is easy: if you are there with at least 10 percent battery, you are done (time equals 0). If you somehow got there with less than 10 percent, that is a failure state.

**Work Backwards**
Now step backward to mile 950, then 900, then 850, and so on. At each position, for each possible battery level, we calculate: "If I am here with this much battery, what is the fastest way to finish?"

The trick is that by the time we evaluate mile 800, we have already solved mile 850, 900, 950, and 1000. So when we ask "should I stop at mile 850 and charge to 60 percent?", we can instantly look up "how long does the rest of the trip take from mile 850 with 60 percent battery?"—we already computed it.

This cascades backward. By the time we reach the starting position, we've solved every possible intermediate state.

**Extract the Solution**
Once the table is full, look up mile 0 with 100 percent battery (our starting condition). That entry tells us the minimum trip time. Then trace forward through the stored decisions: "from here we should drive to mile 200 and charge to 52.5 percent, then from there drive to mile 400 and charge to 53 percent," and so on.

#### 3.2.4 Stop Minimization Strategy

Some drivers care more about minimizing stops than shaving off minutes. Strategy 2 handles this with a two-pass approach.

**First Pass: Count the Minimum Stops**
Run a greedy simulation: start driving, and every time you're about to run out of battery, stop at the farthest charger you can reach and fill up to 100%. Count how many times you stopped. This greedy approach won't give you the fastest time, but it will tell you the theoretical minimum number of stops needed (let's say 4).

**Second Pass: Optimize Time with That Many Stops**
Now run the dynamic programming algorithm again, but add a constraint: you must use exactly four stops, no more, no less. The table gains a third dimension: it now tracks position, battery level, and "stops used so far." 

When evaluating options, we only consider moves that keep us on track to use exactly four stops. If you have already used all four, your only choice is to drive straight to the end. If you have not, you must stop at a charger before reaching the destination. This guarantees the minimum number of stops while optimizing charging behavior at each stop for time.

#### 3.2.5 Computational Complexity

How long does this take to run? For a 1,000-mile trip with chargers every 50 miles and 0.5 percent battery resolution, we have roughly:
- 20 position states (every 50 miles)
- 200 battery states (0.5 percent increments from 10 to 100 percent)
- At each state, we consider about 20 possible chargers to visit
- For each charger, we try 200 possible charge levels

That is 20 × 200 × 200 × 20 = 16 million operations. Sounds like a lot, but modern computers handle this easily. The algorithm runs in less than a second on a typical laptop, fast enough for an interactive web calculator. Users can adjust parameters and see results instantly.

Memory-wise, we need to store the solution for each (position, battery level) pair—about 4,000 entries. That is trivial by today's standards.

### 3.3 Data Sources and Implementation

#### 3.3.1 Vehicle Charging Curve Representation

We need real-world charging data for this to work. Currently, we're using the Electric Vehicle Knowledge Exchange (EVKX), a community-maintained database of measured EV performance. Ideally, this data would come from standardized EPA testing or manufacturer specs, but EVKX gives us publicly available, reasonably consistent measurements across dozens of vehicles. It's the best we have right now.

The data file (XML format) contains two sections:

**Basic Vehicle Info**
Name, highway range, and the speed at which that range applies. For the Volkswagen ID.4, that is 239 miles at 70 mph. Note this is highway-specific range, not the combined city/highway EPA number—highway driving is less efficient.

**Charging Curve Data**
A table with one row for each battery percentage (0 through 100 percent). Each row records:
- Current battery level
- Charging power at that level (kilowatts)
- Cumulative time to charge from empty to this level (minutes)
- Cumulative energy delivered (kilowatt-hours)

For example, the ID.4 at 50 percent battery receives 126 kW of power, and getting from 0 to 50 percent takes 18.75 minutes total.

When we need the time to charge from, say, 20 to 50 percent, we just subtract: 18.75 minutes (cumulative to 50 percent) minus however many minutes to 20 percent gives us the duration of that charging session. Linear interpolation handles battery levels between the measured percentages.

#### 3.3.2 Charging Curve Characteristics

The ID.4's charging curve follows a pattern typical of lithium-ion electric vehicles, exhibiting four distinct phases. From 0 to 10 percent state of charge, power ramps up as the battery management system initiates thermal conditioning. Between 10 and 40 percent, the vehicle maintains peak power plateau around 125 to 140 kW, representing optimal charging conditions. From 40 to 80 percent, charging power begins declining to protect battery longevity, dropping from 125 kW to approximately 73 kW. Above 80 percent, power plummets dramatically to 20 to 30 kW as the battery approaches full capacity.

These charging dynamics create counterintuitive optimization outcomes. Charging from 10 to 40 percent requires approximately 15 minutes, while charging from 80 to 100 percent demands an additional 32 minutes. The final 20 percent of capacity takes longer to fill than the first 30 percent. Consequently, optimal strategies often involve more frequent stops with charging sessions terminating at 50 to 60 percent state of charge, maximizing time spent in the high-power charging region while avoiding the slow taper zone entirely.

#### 3.3.3 Standardized Trip Parameters

To ensure reproducibility and comparability across vehicles, the metric uses standardized conditions:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Trip distance | 1,000 miles | Represents long-distance travel threshold |
| Starting SoC | 100% | Full charge assumption |
| Ending SoC | 10% minimum | ~20-30 miles reserve |
| Highway speed | 70 mph | Typical interstate cruising |
| Charger spacing | 50 miles | Reasonable infrastructure density |
| Minimum SoC | 10% | Safety margin to reach charger |
| Detour distance | 1 mile | Combined exit/entrance distance |

These parameters can be adjusted for sensitivity analysis or specific use cases, but standardization enables direct vehicle-to-vehicle comparison.

---

## 4. Results: Volkswagen ID.4 Case Study

### 4.1 Vehicle Specifications

The Volkswagen ID.4 is a compact crossover electric vehicle featuring a 77 kWh usable battery capacity and 400V electrical architecture. The vehicle achieves an EPA combined range rating of 275 miles, though highway-specific range at 70 mph decreases to 239 miles due to reduced regenerative braking and higher aerodynamic loads. Peak DC fast charging capability reaches 135 kW under optimal conditions. The single rear motor produces 201 horsepower in a rear-wheel drive configuration. The relatively high curb weight of approximately 4,600 lbs combined with crossover aerodynamics yields moderate highway efficiency of approximately 2.8 mi/kWh at 70 mph.

### 4.2 Optimization Results

Applying the time minimization algorithm (Strategy 1) with standardized parameters yields a total travel time of 14.83 hours for the 1,000-mile journey. This comprises four charging stops, 1.58 hours (95 minutes) of total charging time, 14.29 hours (857 minutes) of driving time, and 0.20 hours (12 minutes) of detour overhead. Table 1 presents the detailed charging stop locations and durations.

**Charging Stop Details**:

| Stop | Location (mi) | Arrive SoC | Depart SoC | Charge Time (min) |
|------|---------------|------------|------------|-------------------|
| 1    | 200           | 16.2%      | 52.5%      | 18.3              |
| 2    | 400           | 16.8%      | 53.0%      | 18.5              |
| 3    | 600           | 16.8%      | 53.0%      | 18.5              |
| 4    | 800           | 16.8%      | 53.0%      | 18.5              |
| 5    | 1000 (arrive) | 10.9%      | —          | —                 |

**Table 1.** Optimal charging stop locations and durations for Volkswagen ID.4 on standardized 1,000-mile trip.

The results reveal four key characteristics of the optimal solution. First, after the initial stop, the algorithm converges to a repeating pattern of arriving at approximately 17 percent state of charge and charging to approximately 53 percent. This pattern represents the optimal balance between minimizing time spent in low-power charging regions, maximizing distance between stops, and avoiding excessive charging into the power taper region. Second, all charging sessions occur within the 17 to 53 percent state of charge range where the ID.4 maintains 115 to 135 kW charging power. The algorithm correctly avoids charging beyond approximately 55 percent where power begins substantial decline. Third, arriving at chargers with only approximately 17 percent state of charge (40 miles remaining) maximizes driving distance per stop while maintaining the 10 percent safety margin. This aggressive strategy differs substantially from typical human behavior but achieves global optimality. Fourth, the middle three stops exhibit identical behavior, reflecting the problem's inherent symmetry once the trip is underway.

### 4.3 Comparison with Alternative Strategies

**Strategy 2: Minimum Stops**

Running the stop minimization algorithm:
- **Minimum stops required**: 4 (same as Strategy 1)
- **Total travel time**: 14.83 hours (identical)

In this case, time minimization naturally found the minimum-stop solution. This occurs because the ID.4's range (~239 miles @ 70 mph) and the 50-mile charger spacing create a scenario where adding extra stops provides no benefit.

**Strategy 3: Conventional Window (20-80%)**

Constraining charging sessions to begin between 20-80% SoC:
- **Number of stops**: 5
- **Total travel time**: 15.71 hours
- **Time penalty**: +53 minutes (+6.0%)

The additional stop arises because the 20% lower bound prevents arriving as empty, reducing usable range per segment. The upper bound of 80% forces charging into the taper region, increasing session duration.

### 4.4 Sensitivity Analysis

**Charger Spacing Impact**:

| Spacing (mi) | Stops | Time (hrs) | Notes |
|--------------|-------|------------|-------|
| 25           | 4     | 14.67      | Closer chargers enable shorter sessions |
| 50           | 4     | 14.83      | Baseline scenario |
| 75           | 5     | 15.21      | Forced longer charging sessions |
| 100          | 6     | 16.14      | Range becomes limiting factor |

**Starting SoC Impact**:

| Start SoC | Stops | Time (hrs) | First Stop (mi) |
|-----------|-------|------------|-----------------|
| 70%       | 5     | 15.24      | 150             |
| 80%       | 5     | 15.12      | 170             |
| 90%       | 4     | 14.94      | 190             |
| 100%      | 4     | 14.83      | 200             |

Lower starting SoC forces earlier first stops, potentially requiring an additional stop overall.

### 4.5 Practical Implications

The 14.83-hour result for 1,000 miles represents an effective speed of 67.5 mph, accounting for both the actual 70 mph driving speed and approximately 2.5 mph equivalent overhead from charging and detours. For comparison, a conventional gasoline vehicle completing the same trip with a single 5-minute fuel stop would require approximately 14.3 hours, yielding a 30-minute time penalty (3.5 percent) for the electric vehicle.

This relatively modest penalty reflects three factors: efficient utilization of the high-power charging region, short charging sessions averaging 18 to 19 minutes, and strategic stop placement maximizing driving segments between charges. However, these results assume ideal conditions including chargers available every 50 miles with no queuing, advertised charging speeds achieved consistently, and absence of traffic, adverse weather, or route-specific terrain effects. Real-world performance may vary by 20 to 30 percent depending on actual operating conditions.

---

## 5. Discussion

### 5.1 Metric Interpretation

The standardized 1,000-mile travel time metric provides an intuitive, single-number comparison for EV long-distance capability. Unlike range alone (which ignores charging speed) or peak charging power alone (which ignores efficiency), this metric naturally integrates all relevant factors:

**Example comparison** (hypothetical):
- **Vehicle A**: 300-mile range, 150 kW peak charging → 14.5 hours
- **Vehicle B**: 250-mile range, 250 kW peak charging → 14.2 hours

Despite lower range, Vehicle B's superior charging speed yields better road trip performance. This non-obvious result would be difficult for consumers to predict without computational tools.

### 5.2 Relationship to Existing Tools

Our approach complements rather than replaces trip-specific route planners like A Better Route Planner (ABRP). Key distinctions:

**ABRP and similar tools**:
- Optimize specific real-world routes with actual charger locations
- Account for elevation changes, traffic, weather, real-time charger availability
- Provide navigation-ready instructions
- Results vary by route, season, departure time

**Standardized metric (this work)**:
- Provides vehicle-independent comparison under controlled conditions
- Enables "apples-to-apples" evaluation across models
- Computationally lightweight (runs in browser)
- Results are reproducible and reportable

The standardized metric serves a similar role to EPA fuel economy ratings: not a prediction for every trip, but a consistent basis for comparison.

### 5.3 Algorithm Advantages

The dynamic programming approach offers several advantages over heuristic methods. First, dynamic programming guarantees finding the true minimum time solution within discretization limits, whereas greedy heuristics may converge to local optima. Second, the algorithm naturally accounts for state-dependent charging curves without requiring linearization or approximation. Third, hard constraints such as minimum state of charge and end-of-trip requirements are enforced systematically rather than through penalty functions. Fourth, the decisions table provides full visibility into the optimization logic, enabling users to understand why specific charging strategies emerge. Fifth, additional constraints including charger-specific power limits, battery degradation, or time-of-day pricing can be incorporated by modifying the value function structure.

### 5.4 Limitations and Assumptions

Several simplifying assumptions affect result applicability to real-world conditions. The model assumes infrastructure uniformity with chargers at regular intervals delivering consistent power. Real charging networks exhibit uneven geographic distribution with dense coverage in urban corridors but sparse availability in rural areas, variable power levels ranging from 50 kW to 350 kW intermixed across locations, and availability constraints from occupied or malfunctioning units.

Regarding driving conditions, the model employs constant speed on flat terrain, whereas real trips involve speed variations from traffic, weather, and construction, elevation changes that dramatically increase energy consumption in mountainous regions, and temperature effects that can reduce range by 20 to 40 percent in cold weather.

The charging model assumes immediate session initiation and advertised power delivery. Reality includes initialization delays from payment processing and vehicle-charger handshaking protocols, power sharing when multiple vehicles use the same charging station simultaneously, and battery temperature effects where cold or hot batteries charge at reduced rates.

From a human factors perspective, the algorithm optimizes purely for time, potentially recommending very short charging sessions of 15 to 20 minutes that may not align with meal or restroom break needs, arriving at chargers with very low state of charge providing minimal safety margin for unexpected conditions, and routing past chargers that would offer greater convenience for non-temporal reasons. Despite these limitations, the metric provides a consistent, reproducible foundation for comparative vehicle analysis.

### 5.5 Applications and Future Extensions

For consumers, the metric simplifies electric vehicle selection by reducing the cognitive load of evaluating multiple interdependent specifications, providing intuitive context through hours-to-travel rather than abstract kilowatt ratings, and enabling direct vehicle comparisons expressed as comparable travel times. For researchers and analysts, the metric enables systematic study of how vehicle characteristics affect real-world travel capability, facilitates quantitative comparison across vehicle models and generations, identifies the relative importance of range versus charging speed in different scenarios, and tracks technological progress in the electric vehicle industry over time. For manufacturers, the metric reveals optimization opportunities regarding whether range or charging speed represents the limiting factor, enables benchmarking against competitors on real-world use cases, and guides engineering trade-offs between battery size and charging power capability.

Several enhancements could improve the model's realism and applicability. Incorporating stochastic charger availability would require probabilistic modeling of charger downtime and contingency planning. Modeling variable charger power would capture heterogeneous charging networks with different power levels at different locations. Accounting for battery degradation would incorporate capacity fade and power reduction over vehicle lifetime. Multi-objective optimization could generate Pareto-frontier analysis balancing time, electricity cost, and battery health. Weather integration would adjust range calculations based on temperature, wind, and precipitation. Route-specific terrain modeling would replace the flat-route assumption with actual elevation profiles. User preference modeling would allow weighting of stop duration preferences, balancing fewer longer stops against more frequent shorter stops.

---

## 6. Conclusion

We have presented a dynamic programming framework for generating a standardized metric of electric vehicle long-distance travel performance. By optimizing charging stop locations and durations for a controlled 1,000-mile scenario, the algorithm produces a single, interpretable value—total travel time—that integrates vehicle range, energy efficiency, and charging speed characteristics.

The case study of the Volkswagen ID.4 demonstrates the methodology's ability to identify non-intuitive optimal strategies, such as consistently charging to only 53% SoC to exploit the high-power region of the charging curve. The algorithm finds this globally optimal solution efficiently, executing in under one second on consumer hardware.

This standardized metric addresses a critical gap in EV consumer information. While existing tools like A Better Route Planner excel at trip-specific routing, they cannot provide the consistent, reproducible comparison that consumers need when evaluating vehicles. Our metric serves the analogous role to EPA fuel economy ratings, offering a reliable basis for comparison while acknowledging that individual trip results will vary.

The methodology is extensible, transparent, and computationally efficient, making it suitable for public-facing tools, policy analysis, and research applications. As EV technology continues to advance and charging infrastructure expands, this framework provides a consistent lens for tracking progress in real-world travel capability.

**Data and Code Availability**: The algorithm implementation and vehicle data are available at [repository URL] under an open-source license, enabling reproducibility and community extensions.

**Policy Implications**: This standardized metric can inform consumer decision-making, guide manufacturer development priorities, and support regulatory efforts to improve EV consumer information standards.

**Limitations**: Results assume ideal charging infrastructure availability and weather conditions. Real-world performance may vary by 20 to 30 percent depending on route-specific factors, weather, and infrastructure conditions.

**Future Research**: Extensions should address stochastic charger availability, heterogeneous charging networks, battery degradation effects, and multi-objective optimization incorporating cost and battery health considerations.

---

## CRediT Author Contribution Statement

**Aaron Sobel**: Conceptualization, Methodology, Software, Formal analysis, Data curation, Writing – original draft, Writing – review and editing, Visualization

**Jarrod Brown**: Conceptualization, Methodology, Writing – review and editing, Supervision

---

## Declaration of Competing Interests

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

---

## Declaration of Generative AI and AI-Assisted Technologies in the Writing Process

During the preparation of this work, the authors used GitHub Copilot (code completion assistant) to support algorithm implementation and ChatGPT (OpenAI) to assist with literature review organization and manuscript editing for clarity and grammar. After using these tools, the authors reviewed and edited the content as needed and take full responsibility for the content of the published article.

---

## Acknowledgments

This work was conducted as part of the U.S. Environmental Protection Agency's research on electric vehicle technologies and consumer information systems. The authors thank the Office of Transportation and Air Quality for supporting this research. Vehicle charging data was obtained from the Electric Vehicle Knowledge Exchange (EVKX) community database. The views expressed in this article are those of the authors and do not necessarily represent the views or policies of the U.S. Environmental Protection Agency.

---

## References

A Better Route Planner, 2024. EV trip planning and routing. https://abetterrouteplanner.com (accessed March 2024).

Brooker, A., Gonder, J., Wang, L., Wood, E., Lopp, S., Ramroth, L., 2015. FASTSim: A model to estimate vehicle efficiency, cost and performance. SAE Technical Paper 2015-01-0973. https://doi.org/10.4271/2015-01-0973.

Electric Vehicle Knowledge Exchange (EVKX), 2024. Volkswagen ID.4 Pro charging curve. https://evkx.net/models/volkswagen/id.4/id.4_pro/chargingcurve/ (accessed March 2024).

Neubauer, J., Wood, E., 2014. The impact of range anxiety and home, workplace, and public charging infrastructure on simulated battery electric vehicle lifetime utility. J. Power Sources 257, 12-20. https://doi.org/10.1016/j.jpowsour.2014.01.075.

Nicholas, M., Hall, D., 2018. Lessons learned on early electric vehicle fast-charging deployments. International Council on Clean Transportation, Washington, DC.

Pelletier, S., Jabali, O., Laporte, G., 2016. 50th anniversary invited article—Goods distribution with electric vehicles: Review and research perspectives. Transp. Sci. 50(1), 3-22. https://doi.org/10.1287/trsc.2015.0646.

U.S. Environmental Protection Agency, 2024. Electric vehicle charging infrastructure trends. EPA-420-R-24-001, Washington, DC.

Wolbertus, R., van den Hoed, R., Maase, S., 2016. Benchmarking charging infrastructure utilization. World Electr. Veh. J. 8(4), 754-771. https://doi.org/10.3390/wevj8040754.

Yang, J., Sun, H., 2015. Battery swap station location-routing problem with capacitated electric vehicles. Comput. Oper. Res. 55, 217-232. https://doi.org/10.1016/j.cor.2014.07.003.

Yi, Z., Bauer, P.H., 2017. Optimal stochastic eco-routing solutions for electric vehicles. IEEE Trans. Intell. Transp. Syst. 19(12), 3807-3817. https://doi.org/10.1109/TITS.2017.2775646.

Zhang, A., Kang, J.E., Kwon, C., 2017. Multi-day scenario analysis for battery electric vehicle feasibility assessment and charging infrastructure planning. Transp. Res. Part C: Emerg. Technol. 75, 132-146. https://doi.org/10.1016/j.trc.2016.12.011.
