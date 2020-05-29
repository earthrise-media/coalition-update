import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import matplotlib.pyplot as plt
import geopandas as gpd
import datetime
import model

st.header("Earthrise Report \\#1")

st.sidebar.markdown("""

**Table of Contents**

---------

1. Data infrastructure
2. Policy
3. Design

""")

st.markdown("""

> Prepared **2020-05-29**.  

Earthrise focuses on the policy, design, and data infrastructure of Earth
observation for climate action.  You can't change what you can't measure.  Our
role in the Coalition has been to support members with data, elevate the role
of Earth observation in policymaking, and assist with the graphic and UI/UX
design for Coalition products.

This simple web app reports on progress to date *and* highlights the
capabilities of Earthrise that can or has already been made available to
Coalition members.

""")

st.subheader("Data infrastructure")

st.markdown("""

Access to satellite data &mdash; both legal and technical &mdash; is
non-trival.  The primary revenue source for commercial imagery providers is
the military, which has much more disposable cash for data procurement.  The
basic infrastructure to access the data was not meant for a broad community of
developers, and especially those developers with scientific intent.  Earthrise
has been developing access and storage patterns for data that facilitate
environmental science and monitoring.  Some of the capabilities are
illustrated below.

**Time series extraction**

> Create long-term time series of derived measures from space-based sensors
&mdash; for both large geographic regions or small areas with high-resolution
imagery.

A common pattern for both point-source and landscape emissions monitoring is
to extract a historical time-series of measurements from satellite-based
sensors.  Consider, as an example, fire monitoring in California. Two critical
variables for predicting wildfire are dead `fuel moisture` and the National
Fire Danger Rating System `burn index`.  

The following graph depicts the average daily fire conditions for all of
California since 1980.  The breakpoint slider helps to find trends and
breakpoints, i.e., abrupt changes in levels or rates in the series. (*The
discontinuity analysis is more relevant for vegetation indices associated with
agriculture or forestry, but this offers a useful demonstration.*)  Note that
the spatial resolution of this dataset is 4km &mdash; relatively
low-resolution but more than sufficient to identify regional, long-term
trends.

""")

@st.cache(persist=True)
def load_data(plot=True):

	firedf = gpd.read_file('data/a000000af.gdbtable')
	firedf = firedf[(firedf.YEAR_.notna()) & (firedf.YEAR_ != '')]
	firedf['YEAR'] = gpd.pd.to_numeric(firedf.YEAR_)

	bidf = pd.read_pickle("data/nfdrs.pkl")

	return firedf, bidf

fire_df, nfdrs_df = load_data()

def convert_time(x):
	utc_time = datetime.datetime.strptime(x, "%Y-%m-%d")
	epoch_time = (utc_time - datetime.datetime(1970, 1, 1)).total_seconds()
	return epoch_time * 1000


nfdrs_label = st.selectbox(
	'Variable',
	['fuel moisture (percent)', 'burn index (0-100)']
)


break_point = st.slider(
	'Regression discontinuity break point (year)',
	1980, 2020, 1990
)

vardict = {'fuel moisture (percent)': 'fm100','burn index (0-100)': 'bi'}
nfdrs_var = vardict[nfdrs_label]

vis = {'fm100': [0, 30], 'bi': [0, 80]}

t0 = convert_time(nfdrs_df.date.iloc[0])
t1 = convert_time(nfdrs_df.date.iloc[-1])
break_t = convert_time('%s-01-01' % break_point)

df1 = nfdrs_df[nfdrs_df.date < '%s-01-01' % break_point]
df2 = nfdrs_df[nfdrs_df.date >= '%s-01-01' % break_point]

 
# Fire index
nfdrs_data_1 = alt.Chart(df1).mark_circle(
	color="#A9BEBE", 
	size=1.5
).encode(
	x=alt.X(
		'date:T',
		axis=alt.Axis(
			title=""
		)
	),
	y=alt.Y(nfdrs_var, axis=alt.Axis(title=""))
)

nfdrs_data_2 = alt.Chart(df2).mark_circle(
	color="#A9BEBE", 
	size=1.5
).encode(
	x=alt.X(
		'date:T',
		axis=alt.Axis(
			title=""
		)
	),
	y=alt.Y(nfdrs_var, axis=alt.Axis(title=""))
)


line_1 = nfdrs_data_1.transform_regression(
	'date', 
	nfdrs_var,
	extent=[t0, break_t]
).mark_line(
	color='#e45756'
)

line_2 = nfdrs_data_2.transform_regression(
	'date', 
	nfdrs_var,
	extent=[break_t, t1]
).mark_line(
	color='#e45756'
)

st.altair_chart(
	nfdrs_data_1 + nfdrs_data_2 + line_1 + line_2,
	use_container_width=True
)

st.markdown(""" 

> *There is a statistically significant time trend for both variables.* 
Aggregate fuel moisture has decreased by roughly 15 percent since 1980 and the
burn index has increased by roughly 15 percent.

This example demonstrates the ease by which we can create and analyze long
time series, aggregated for large areas.  Earthrise has developed some rough
web service APIs to support Coalition members. 

It is helpful to link these time series to the explicitly geographic source. 
Consider, now, the time series of wildfire extent for California over the past
100 years. These trends in burn index and fuel moisture track with the
long-term historical trends in wildfire extent and prevalence.  

""")

st.image(
	"data/ca.jpg", 
	use_column_width=True, 
	caption="Fires in CA, 1920-2020, darker red indicates more recent fires"
)

st.markdown(""" 

This large dataset can be reformatted into a more comprehensible visualization
&mdash; at least for quick-glance policymakers.  The interaction is important
for both policymakers and reporters.  Ultimately, for the Coalition, it is
helpful to frame development in terms of the final data interactions that have
demonstrated significant impact.

""")

cause_dict = {
	"Lightning": 1,
	"Equipment Use": 2,
	"Smoking": 3,
	"Campfire": 4,
	"Debris": 5,
	"Railroad": 6,
	"Arson": 7,
	"Playing with fire": 8,
	"Miscellaneous": 9,
	"Vehicle": 10,
	"Powerline": 11,
	"Unknown / Unidentified": 14,
	"Escaped Prescribed Burn": 18
}

window = st.slider(
	'Moving average window (years)',
	3, 20, 15
)

cause_option = st.selectbox(
	'Cause',
	["All"] + list(cause_dict.keys())
)


if cause_option != 'All':
	fire_df = fire_df[fire_df.CAUSE == cause_dict[cause_option]]

tot = fire_df.groupby('YEAR')['GIS_ACRES'].sum()
tot = gpd.pd.DataFrame(tot).reset_index()
tot.columns = ["year", "acres"]
tot = tot[tot.year > 1910]
tot.year = pd.to_datetime(tot.year, format='%Y')


line_smooth = alt.Chart(tot).mark_line(
	color='#e45756'
).transform_window(
	rolling_mean='mean(acres)',
	frame=[-window, 0]
).encode(
	x=alt.X('year:T', axis=alt.Axis(title="")),
	y=alt.Y('rolling_mean:Q', axis=alt.Axis(title="Burned area (acres)"))
).interactive()

st.altair_chart(line_smooth, use_container_width=True)




st.markdown("""

**Tools for journalists**: Lessons from COVID modeling

> Run complicated models in the browser, and create interactive and embeddable
widgets for reporters.

Earthrise supported Tom Frieden's pandemic lead and Johns Hopkins
epidemiologists with math &mdash; because that's the world we live in now. 
This is relevant because [Covidtracker](https://www.covidtracker.com/) is the
most widely used online data dashboards in human history.  Our recent
experience in assisting high-profile scientists and policymakers has served as
product discovery for data dashboards.

We developed a model, code, and visualizations to support policymakers in
understanding the impact of lifting restrictions like stay-at-home orders.  We
are armchair epidemiologists &mdash; the worst kind.  However, our role was
just to do the math and build the interactive widgets.  The model is detailed
below, for posterity's sake.  It is an age-stratefied compartmental model, an
extension on the standard SEIR model that is used by basically every other
armchair epidmiologist &mdash; and most of the pros, too.

Our multidimensional generalization of the SEIR compartmental model
can be represented mathematically as follows:

""")

eqnarray = r"""
	\begin{array}{lll}
		\frac{dS_a}{dt} &=& - S_a\; \sum_b \beta c_{ab}(t) (I_b + M_b)/ N_b \\
		\\
		\frac{dE_a}{dt} &=& S_a\; \sum_b \beta c_{ab}(t) (I_b + M_b)/ N_b - \alpha E_a\\
		\\
		\frac{dI_a}{dt} &=& \alpha (1-\kappa_a) E_a - \gamma I_a\\
		\\
        \frac{dM_a}{dt} &=& \alpha \kappa_a E_a - \delta M_a\\
        \\
		\frac{dR_a}{dt} &=& \gamma I_a \\
        \\
        \frac{dD_a}{dt} &=& \delta M_a\\

	\end{array}{}
"""

st.latex(eqnarray)

import shapely.geometry

START_DAY, END_DAY = 0, 300
initial_infected = .001

TOTAL_POPULATION = 1e6
population = TOTAL_POPULATION * model.WORLD_POP["Americas"]
pop_0 = np.array([[f * (1 - 2 * initial_infected), f * initial_infected,
					   f * initial_infected, 0, 0, 0] for f in population])

npi_intervals = {
    'School closure':
        st.slider('Schools closed', START_DAY, END_DAY, (30, 70)),
    'Cancel mass gatherings':
        st.slider('Cancellation of mass gatherings',
                  START_DAY, END_DAY, (30, 80)),
    'Shielding the elderly':
        st.slider('Shielding the elderly',
                  START_DAY, END_DAY, (30, 100)),
    'Quarantine and tracing':
        st.slider('Self-isolation, quarantine, and contact tracing',
                  START_DAY, END_DAY, (70, 200))
}

shelter_interval = (20, 20)

def _trim(interval, interval_to_excise):
    l1 = shapely.geometry.LineString([[x,0] for x in interval])
    l2 = shapely.geometry.LineString([[x,0] for x in interval_to_excise])
    diff = l1.difference(l2)
    if type(diff) == shapely.geometry.linestring.LineString:
        coords = [int(x) for x,_ in diff.coords]
        coords = [coords] if coords else []
    elif type(diff) == shapely.geometry.multilinestring.MultiLineString:
        coords = [[int(x) for x,_ in segment.coords] for segment in diff.geoms]
    return coords

selected_npis, intervals = [], []
for k,v in npi_intervals.items():
    coords = _trim(v, shelter_interval)
    for c in coords:
        selected_npis.append(k)
        intervals.append(c)
            
selected_npis.append('Shelter in place')
intervals.append(shelter_interval)

contact_matrices, epoch_end_times = model.model_input(
    model.CONTACT_MATRICES_0["Americas"],
    intervals,
	selected_npis,
    END_DAY-START_DAY)

res = model.SEIRModel(contact_matrices, epoch_end_times)

df, y = res.solve_to_dataframe(pop_0.flatten(), detailed_output=True)
infected = df[df["Group"] == "Infected"]

chart = alt.Chart(infected).mark_line(
	color="#e45756").encode(
		x=alt.X('days', axis=alt.Axis(title='Days')),
		y=alt.Y('pop', axis=alt.Axis(title=''),
                scale=alt.Scale(domain=(0,TOTAL_POPULATION/10))))

st.markdown('Infections (per million)' )

st.altair_chart(chart, use_container_width=True)


st.write("""

The subscripts (a,b) index the (age) cohorts, while alpha, beta,
gamma, and delta are the inverse incubation period, the probability of
transmission given a contact between two people, the inverse duration
of infection, and the inverse time to death, respectively. The matrix
c_ab is the *contact matrix*, encoding the average number of daily
contacts a person in cohort a has with people in cohort b. The vector
kappa_a encodes the infection fatality rates for each cohort.

Now, regarding the relevance to the Coalition.  Both policymakers and
reporters needed a way to interact with complicated differential equations,
without needing to understand the math.  They also needed the interactions to
be customizable and embeddable.  The fact that we wrote these visualizations
in Python, for example, held up publication in Reuters by weeks.  

> *Any dashboard should offer cutomizable cards that are easily embedded in
third-party websites or reports.*

The way we share data is changing.  A dashboard that just presents data in a
map will go nowhere &mdash; or at least not nearly as far as one that caters
to the users.

""")  

st.markdown("""

**Interact with individual images**

""")

st.subheader("Policy")

st.markdown("""

Our primary focus has been on Earth observation (EO) data policy in the next
U.S. administration &mdash; how to finance, collect, and activate remotely
sensed information for climate policy.

1. **Earth Observation for Sensible Climate Policy**.  We are contributing to
the memos for the Biden transition team on Earth Observation through both the
Center for American Pogress and the Day One Project. The memos describe
day-one actions that the next Administration can take to increase the value of
Earth observation to inform federal climate policy. 

2. **Center for Strategic and International Studies Workshops**.  We are
assembling policy wonks, scientists, and data engineers at a workshop
sponsored by CSIS to answer questions like, "*What data are required but
currently unavailable to make a critical policy decision right now*?" We will
invite Coalition members to participate.  The objective of the workshop that
is most aligned with the Coalition's mission is to identify data and data
products that are currently bottlenecks for sensible climate policy, both
domestic and international.

3. **Policy perspectives**.  Earth observation &mdash; the most basic data
about our home planet &mdash; is not nearly as ubiquitous as it could and
should be.  In fact, sometimes, it is unnecessarily positioned as competitive
with other public science objectives.  Other times, it is just forgotten in
areas of education, infrastructure planning, and other critical areas in both
the public and private sector.  We are working on helping define a more
productive narrative through popular press, including interviews with the New
York Times, Netflix, Reuters, and many other high-profile outlets.

4. **Tracking existing sensors**. We are trying to maintain a canonical list
of sensors that are useful to the Coalition's mission.  [This is on
Notion](https://www.notion.so/climatei/787bd173c7fa4fe4ab78365d360ab343?v=774c90da8d2b48208b6feaf362e224c8).
It is exciting to watch other members contribute to this list as a shared
resource.

The objectives for the Earthrise policy track are two-fold.  First, increase
the support for meaningful data collection about our home planet.  Second,
discover exactly what data policy makers urgently need to make better policy
around climate change mitigation and adaptation.

""")

st.subheader("Design")

st.markdown("""

Earthrise is currently supporting the logo design and brand identity for the
Coalition.  We will run a series of logo experiments on the final list of
names, and submit the results to the coalition for review.

""")

image_num = st.slider(
	'Concept Number',
	1, 6, 3
)

st.image(
	"%s.jpg" % image_num,
	use_column_width=True
)

st.markdown("""

The next phase includes the design of the user interface for the Coalition
dashboard.  Early, *early* wireframes of the dashboard are below.  These are
about as well-baked as the name "Theo" for the coalition &mdash; meant only to
solicit more granular responses.  We will ultimately utilize the time of our
pro graphic designers rather than UI/UX designers for the dashboard.

The two most important features are:

1. Embeddable widgets that are easily customized for a particular sector, time
period, and geographic region.

2. Sector-specific "slices" of the emissions data, starting with the big four
or five.

""")

st.image(
	"dashboard1.png",
	use_column_width=True,
	caption="Proposed landing page"
)

st.image(
	"dashboard2.png",
	use_column_width=True,
	caption="Initial overview page"
)

st.image(
	"dashboard3.png",
	use_column_width=True,
	caption="Sector-specific page"
)


st.markdown("""

The high-fidelity designs will help to determine the final data format for
member submissions, hopefully facilitating collaboration and the design and
development of shared infrastructure.

""")
