import pandas as pd
import textwrap
import us

from ... import ArcGIS
from .... import DatasetBaseNoDate


class OKTulsa(DatasetBaseNoDate, ArcGIS):
    """
    Tulsa, Oklahoma publishes their county level data in a dashboard that can
    be found at:

    https://tcchd.maps.arcgis.com/apps/opsdashboard/index.html#/ebb119cd215b4c57933b7fbe477e7c30

    This retrieves the data from the ArcGIS API
    """

    ARCGIS_ID = "yHSoWow4TMdKqS8y"
    source = (
        "https://tcchd.maps.arcgis.com/apps/opsdashboard/index.html#/"
        "ebb119cd215b4c57933b7fbe477e7c30"
    )
    state_fips = int(us.states.lookup("OK").fips)

    def _insert_query(self, df, table_name, temp_name, pk):
        return ArcGIS._insert_query(self, df, table_name, temp_name, pk, on_name=True)

    def get(self):
        # Note: Service=Covid19Coronavirusdata_V3_View seems to have caser by
        #       case data
        df_cd = self.get_all_sheet_to_df("COVID19_Regions_V3_View", 0, 3).drop(
            columns=["FID", "Latitude", "Longitude"]
        )
        df_hosp = self.get_all_sheet_to_df("COVID19Hospitalizations_View", 0, 3).drop(
            columns=["FID", "Latitude", "Longitude"]
        )
        df = df_cd.merge(df_hosp, on=["Date", "County"], how="outer")

        # Divide by 1000 because arcgis spits time out in epoch milliseconds
        # rather than epoch seconds
        df["Date"] = df["Date"].map(lambda x: pd.datetime.fromtimestamp(x / 1000))

        # Rename columns
        crenamer = {
            "Date": "dt",
            "County": "county",
            "TulsaCounty": "cases_total",
            "Co_Deaths": "deaths_total",
            "Co_Recovered": "recovered_total",
            "Co_Active": "active_total",
            # "Tulsa_Hosp_Y": "hospitalized_cumulative"
            # "Tulsa_Hosp_N": "not_hospitalized_cumulative"
            # "Tulsa_Hosp_U": "???hospitalized_cumulative"
            "In_Hospital": "hospital_beds_in_use_covid_total",
            "Admissions": "hospital_beds_in_use_covid_new",
        }
        df = df.rename(columns=crenamer)

        df = (
            df.loc[:, list(crenamer.values())]
            .melt(
                id_vars=["dt", "county"], var_name="variable_name", value_name="value",
            )
            .dropna()
        )
        df["vintage"] = pd.Timestamp.utcnow().normalize()

        return df