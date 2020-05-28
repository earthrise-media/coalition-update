import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import matplotlib.pyplot as plt
import geopandas as gpd
import datetime

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
of Earth observation in policymaking, and 

This simple web app reports on progress to date *and* highlights the
capabilities of Earthrise for Coalition members.

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
for both policymakers and reporters.

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

Earthrise supported Tom Frieden's pandemic lead and Johns Hopkins
epidemiologists with math &mdash; because that's the world we live in now. 
This is relevant because [Covidtracker](https://www.covidtracker.com/) is the
most widely used online data dashboards in human history.  Our work helps
frame the requirements for 


**Interact with individual images**
""")

st.subheader("Policy")

st.markdown("""

Our primary focus has been on EO data policy in the next U.S. administration.

1. **Earth Observation for Sensible Climate Policy**.   CAP, Day One.

2. **Center for Strategic Roundtable**.  Next step to invite members for the
EO data infrastructure piece.

3. **Policy perspectives**.  Interviews that help show leadership in EO
without pitting planetary science against EO.  Reframing the narrative.

4. 

""")

st.subheader("Design")



