# Capacity update process

## Table of contents
- [Context](#context)
- [Capacity source](#capacity_sources)
- [Capacity update process](#capacity_update_process)

  - [Format of the capacity configuration](#format)
  - [Opening a PR](#PR)
  - [The zone capacity can be updated automatically](#automatic_update)
  - [The zone capacity is updated manually](#manual_update)

- [Technical requirements for adding a new data source](#technical_requirements)

## Context <a name="#context"></a>
In  an effort to increase the quality of the data published on our app or API, we have started a whole initiative to enable us to track outliers in the source data.

Over the years, we have noticed that sometimes, real-time data published by the different data sources can be completely outside the distribution of the historical time-series. These data points are outliers and need to be detected before any data processing.

One way to perform outlier detection is to check that each incoming data point is not higher than the installed capacity for a given mode. The power output cannot be above the energy input as the efficiency of power plants is always below 100%. In other words, for a given zone and a given mode, the power production for that mode at any given time cannot exceed the installed capacity for that mode.

**Example**

In 2023, the wind capacity in **DK-DK1** was 5233 MW. The average wind production in the first 3 quarters of 2023 was 1455 MW.

The goal here is to validate each incoming production parser event by comparing each mode production against the installed capacity available in the zone configuration. If a mode production is higher than the installed capacity, the data point will be flagged as an outlier and will be corrected by our data pipelines.

To achieve this goal, we need robust and consistent capacity data. We also need to be able to capture the evolution of capacity data over time. As renewable capacity increases in most zones, this means that the power production will also increase.

## Capacity sources <a name="#capacity_sources"></a>

 Of all electricity data available, capacity is probably the least consistent (eg different reporting standards, different update frequencies, accessibility). A review of available capaicty data was done for this project in order to manage the number of different data sources used for capacity and to ensure that the capacity data has been reviewed and has an overall quality level.

 Limiting the number of sources for capacity data also increases the maintainability of the entire dataset.

 The main organisations that published capacity data are:

 - **[EIA](https://www.eia.gov/electricity/data/eia860/)**: The EIA publishes generator-level specific information about existing and planned generators and associated environmental equipment at electric power plants with 1 megawatt or greater of combined nameplate capacity. This data is available in the EIA API and can be aggregated  by balancing authority.
 - **[EMBER](https://ember-climate.org/)**: EMBER aggregates data from different sources:
    - IRENA for non-fossil generation,
    - Global Energy Monitor for coal and gas generation,
    - World Resource Institue, although this datbase is incomplete is can be used to verify information from the other sources.
 - **[ENTSO-e](https://transparency.entsoe.eu/generation/r2/installedGenerationCapacityAggregation/show)**: Net generation capacity is published on an annual basis on the ENTSO-e Transparency platform. This will be the prefered data source for European zones as the capacity breakdown is more detailed.
 - **[IRENA](https://www.irena.org/Data/Downloads/IRENASTAT)**: For most countries and technologies, the data reflects the capacity installed and connected at the end of the calendar year. Data has been obtained from a variety of sources, including an IRENA questionnaire, official national statistics, industry association reports, other reports and news articles.

In the case of countries divided in subzones, capacity data is collected directly from the main data source. This is the case for Brasil, Australia or Spain for instance.

## Capacity update process <a name="#capacity_update_process"></a>

There are two ways of updating capacity configuration files:

- The zone has a capacity parser
- The update must be done manually.

### Format of the capacity configuration  <a name="#format"></a>
The capacity configuration should include the date from which the value is valid.

For a chosen mode, a data point needs to include the following fields:
- value: the installed capacity for the chosen mode,
- datetime: from this date forward, the value is considered to be the most up-to-date
- source: the data source

This format will enable us to track the evolution of capacity across different zones over time such as the increase of renewables or phase out of fossil power plants.

Looking at the example of DK-DK1 mentioned above, the capacity configuration format would be the following:
```
capacity
├── wind
    ├── datetime: "2023-01-01"
    ├── source: "ENTSOE"
    └── value: 5233
```
### Opening a PR  <a name="#PR"></a>
Before opening a PR to update capacity data, you should check the following:

- **Do not update all capacities at once!** Smaller PRs will help us make sure that no error slips through the cracks. We recommend updated a few zones at once or by group of zones (EIA, ENTSOE, EMBER, IRENA etc.)
- **The new data points are consistent with the previous ones.** Big breaks in trends are rare for capacity data. You should check whether the variation between two data points is realistic. We expect that renewable capacity will increase in the coming years and fossil capacity to decrease,so these are patterns to look out for.
- **Reference main changes in the PR description**. If you spot a major change in values, please mention it and verify it. This will make the reviewer's job easier!

### The zone capacity can be updated automatically <a name="#automatic_update"></a>
For some zones, we have developed capacity parsers which collect the data automatically.

The update of capacity configurations can be done in the `contrib` repo using `poetry run capacity_parser`.

The `capacity_parser` function has the following arguments:
<table>
  <thead>
    <tr>
      <th>Argument</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>--zone</td>
      <td>A specific zone (e.g. Dk-DK1)</td>
    </tr>
    <tr>
      <td>--source</td>
      <td>A group of zones (e.g. ENTSOE). The capacity update will run for all the zones that have capacity from this data source </td>
    </tr>
    <tr>
      <td>--target_datetime</td>
      <td> Date for the capacity dat (e.g. "2023-01-01") </td>
    </tr>
    <tr>
      <td>--path</td>
      <td>Path to the data file. In some cases, the data needs to first be downloaded and cannot be directly parsed online. (more below) </td>
    </tr>
  </tbody>
</table>

Here is a list of examples:
```{python}
poetry run capacity_parser --zone DK-DK1 --target_datetime "2023-01-01"
```
```{python}
poetry run capacity_parser --source EIA --target_datetime "2023-06-01"
```
```{python}
poetry run capacity_parser --source EMBER --target_datetime "2022-01-01" --path "/../yearly_full_release_long_format.csv""
```
> **Important note:** For EMBER and IRENA, the --data_path is necessary as the parser reads the data from a csv/xlsx downloaded by the contributor


The following zones can be updated with a parser:
&nbsp;<details><summary>EIA</summary>
  - US-CAL-BANC
  - US-CAL-CISO
  - US-CAL-IID
  - US-CAL-LDWP
  - US-CAL-TIDC
  - US-CAR-CPLE
  - US-CAR-CPLW
  - US-CAR-DUK
  - US-CAR-SC
  - US-CAR-SCEG
  - US-CAR-YAD
  - US-CENT-SPA
  - US-CENT-SWPP
  - US-FLA-FMPP
  - US-FLA-FPC
  - US-FLA-FPL
  - US-FLA-GVL
  - US-FLA-HST
  - US-FLA-JEA
  - US-FLA-SEC
  - US-FLA-TAL
  - US-FLA-TEC
  - US-MIDA-PJM
  - US-MIDW-AECI
  - US-MIDW-LGEE
  - US-MIDW-MISO
  - US-NE-ISNE
  - US-NW-AVA
  - US-NW-BPAT
  - US-NW-CHPD
  - US-NW-DOPD
  - US-NW-GCPD
  - US-NW-GRID
  - US-NW-GWA
  - US-NW-IPCO
  - US-NW-NEVP
  - US-NW-NWMT
  - US-NW-PACE
  - US-NW-PACW
  - US-NW-PGE
  - US-NW-PSCO
  - US-NW-PSEI
  - US-NW-SCL
  - US-NW-TPWR
  - US-NW-WACM
  - US-NW-WAUW
  - US-NW-WWA
  - US-NY-NYIS
  - US-SE-SEPA
  - US-SE-SOCO
  - US-SW-AZPS
  - US-SW-EPE
  - US-SW-GRIF
  - US-SW-PNM
  - US-SW-SRP
  - US-SW-TEPC
  - US-SW-WALC
  - US-TEN-TVA
  - US-TEX-ERCO&nbsp;</details>
&nbsp;<details><summary>EMBER</summary>
  - AR
  - AW
  - BA
  - BD
  - BO
  - BY
  - CO
  - CR
  - CY
  - DO
  - GE
  - GT
  - HN
  - KR
  - KW
  - MD
  - MN
  - MT
  - MX
  - NG
  - PA
  - PE
  - RU
  - SG
  - SV
  - TH
  - TR
  - TW
  - UY
  - ZA&nbsp;</details>
&nbsp;<details><summary>ENTSOE</summary>
  - AL
  - AT
  - BA
  - BE
  - BG
  - CZ
  - DE
  - DK-DK1
  - DK-DK2
  - EE
  - ES
  - FI
  - FR
  - GR
  - HR
  - HU
  - IE
  - LT
  - LU
  - LV
  - ME
  - MK
  - NL
  - NO-NO1
  - NO-NO2
  - NO-NO3
  - NO-NO4
  - NO-NO5
  - PL
  - PT
  - RO
  - RS
  - SI
  - SK
  - UA
  - XK&nbsp;</details>
&nbsp;<details><summary>IRENA</summary>
  - GF
  - IL
  - IS
  - LK
  - NI
  - PF&nbsp;</details>
&nbsp;<details><summary>OPENNEM</summary>
  - AU-NSW
  - AU-NT (only for solar generation)
  - AU-QLD
  - AU-SA
  - AU-TAS
  - AU-VIC
  - AU-WA
&nbsp;</details>
&nbsp;<details><summary>REE</summary>
  - ES
  - ES-CE
  - ES-CN-FVLZ
  - ES-CN-GC
  - ES-CN-HI
  - ES-CN-IG
  - ES-CN-LP
  - ES-CN-TE
  - ES-IB-FO
  - ES-IB-IZ
  - ES-IB-MA
  - ES-IB-ME
  - ES-ML

>**Note**: For the Canary Islands and the Baleares Islands, only total installed capacity is available.
&nbsp;</details>
&nbsp;<details><summary>ONS</summary>

>**Note**: The capacity parser for Brasil only get connected solar capacity. Distributed solar capacity needs to be added manually and can be found here ([ONS - Installed Capacity Dashboard](https://www.ons.org.br/Paginas/resultados-da-operacao/historico-da-operacao/capacidade_instalada.aspx)). See below for more instructions.

  - BR-CS
  - BR-N
  - BR-NE
  - BR-S&nbsp;</details>


The following other zones can also be updated automatically:

- CA-ON
- CA-QC
- CL-SEN
- GB
- MY-WM

### The zone capacity is updated manually <a name="#manual_update"></a>
For the following zones, a capacity parser is not available. You will find the instructions to extract the latest capacity information below. Once the data is collected, the capacity configuration should be updated using the above mentioned format.
&nbsp;<details><summary>CA-SK</summary>
**Main link**: https://www.saskpower.com/Our-Power-Future/Our-Electricity/Electrical-System/System-Map

Capacity data is available in a html table and can be parsed. A parser was not built as we only collect daily data for this parser.
&nbsp;</details>
&nbsp;<details><summary>CH</summary>
Main link: https://www.uvek-gis.admin.ch/BFE/storymaps/EE_Elektrizitaetsproduktionsanlagen/

Capacity is available in a table on the webpage.
&nbsp;</details>
&nbsp;<details><summary>SE</summary>
**Main link**: https://www.svk.se/om-oss/rapporter-och-remissvar/

**Report name**: Kraftbalansen på den svenska elmarknaden, rapport YYYY

The report is published annually and in pdf format.It should be updated at the end of May of the following year.

**Table name**: Tabell 3. Installerad effekt [MW] per kraftslag
&nbsp;</details>
&nbsp;<details><summary>PH</summary>
**Main link**: https://doe.gov.ph/electric-power
>*Disclaimer*: the website is geo-blocked and can only be accessed by using a VPN.

**Report name**: YYYY List of Existing Power Plants in Grid areas for Luzon, Visayas and Mindanao

The report is published every six months and is available in pdf format. The report includes capacity data for all sub-zones for production and battery storage.
&nbsp;</details>
&nbsp;<details><summary>IN</summary>

Capacity is collected from two main sources. Both sources are pdf and revised at least twice a year.

For renewable sources, data is published by the Ministry of New and Renewable Energy

- **Main link**: https://mnre.gov.in/en/physical-progress/
- **Report name**: State-wise RE installed capacity

The data is available at the state level and should be aggregated as follows:
- Northern grid: Delhi, Haryana, Himachal Pradesh, Jammu and Kashmir, Ladakh, Punjab, Rajasthan, Uttar Pradesh, Uttarakhand
- Western grid: Maharashtra, Gujarat, Madhya Pradesh, Chhattisgarh, Goa, Dadra and Nagar Haveli
- Southern grid: Tamil Nadu, Karnataka, Kerala, Andhra Pradesh, Telangana, Pondicherry
- Eastern grid: Bihar, Jharkhand, Odisha, West Bengal, Sikkim
- North-Eastern grid: Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Tripura

> **Note**:
>This report only includes small hydro. Conventional hydro is published on the National Power Portal. Total hydro capacity is the sum of both.

For conventional power generation, data is published by the National Power Portal.

 - **Main link**: https://npp.gov.in/publishedReports
 - **Report name**: All India Installed Capacity of Power Stations (available in pdf and xls)

&nbsp;</details>
&nbsp;<details><summary>FO</summary>
**Main link**: https://www.sev.fo/english/the-power-supply-system

Consider Thermal to be oil generation.
&nbsp;</details>
&nbsp;<details><summary>DK-BHM</summary>

**Main link**: https://reempowered-h2020.com/pilots/bornholm/

**Note**: This source may not be updated in the future. Fossil capacity should not change or be mothballed but wind and solar capacity are likely to increase.
&nbsp;</details>
&nbsp;<details><summary>FR-CO</summary>

**Main link**: https://corse.edf.fr/edf-en-corse/nos-installations-en-corse/nos-moyens-de-production-electrique-en-corse

See data in the section *“La carte au format texte”*

>**Note**: This source may not be updated in the future. Fossil capacity should not change or be mothballed but wind and solar capacity are likely to increase.
&nbsp;</details>
&nbsp;<details><summary>RU</summary>

**Main link**: https://minenergo.gov.ru/node/532

>*Disclaimer*: the website is geo-blocked and can only be accessed by using a VPN

**Table name**: Table 3 Structure of installed capacity of power plants [...]

> **Note**:
> Data has not been updated since 01-01-2020, it would be good to see if an other source exists.
&nbsp;</details>
&nbsp;<details><summary>AU-NT</summary>

Capacity data is available from two different sources.

For conventional power generation:

* **Main link**: https://territorygeneration.com.au/about-us/our-power-stations/

Solar capacity is available on **OPENNEM**, this data can be collected using the OPENNEM parser by doing the following:
- Run `poetry run capacity_parser --zone AU-NT --target_datetime 2023-01-01` and update other capacity manually using the same format
&nbsp;</details>
&nbsp;<details><summary>KR</summary>
> **Note**: Ember does not publish hydro storage capacity. The rest of the data is collected from EMBER. The value for pumped storage should be extracted and added manually to the capacity configuration.

**Main link**:https://www.khnp.co.kr/eng/contents.do?key=414

**Table name**: Pumped-Storage Power Plants

&nbsp;</details>
&nbsp;<details><summary>TW</summary>
> **Note**: Ember does not publish hydro storage capacity. The rest of the data is collected from EMBER. The value for pumped storage should be extracted and added manually to the capacity configuration.

**Main link**: https://www.taipower.com.tw/en/news_noclassify_info.aspx?id=4190&chk=a6afa390-3b52-42eb-bc94-db2afc6cdb6c&mid=4440&param=pn%3d1%26mid%3d4440%26key%3d

**Mode name**: P.S. hydro
&nbsp;</details>
&nbsp;<details><summary>GT</summary>

**Main link**: https://ager.org.gt/wp-content/uploads/

**Guidelines**:
- Navigate the repo to the selected year.
- In the latest months, find the report named `9.-monitor-mensual-mercado-electrico-guatemalteco`
- The data is available in the last section of the report **CAPACIDAD INSTALADA EN EL S.N.I. [POTENCIA EFECTIVA]**

**Mode mapping**:
<table>
  <thead>
    <tr>
      <th>Mode</th>
      <th>Electricity Maps mode</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Hidroeléctrica</td>
      <td>hydro</td>
    </tr>
    <tr>
      <td>Hidroeléctrica GDR</td>
      <td>hydro </td>
    </tr>
    <tr>
      <td>Geotérmica</td>
      <td>geothermal </td>
    </tr>
    <tr>
      <td>Solar Fotovoltaica</td>
      <td>solar </td>
    </tr>
    <tr>
      <td>GDR Fotovoltaica</td>
      <td>solar </td>
    </tr>
    <tr>
      <td>Eólica</td>
      <td>wind </td>
    </tr>
    <tr>
      <td>Turbinas de Vapor</td>
      <td>gas </td>
    </tr>
    <tr>
      <td>Turbinas de Gas</td>
      <td>gas </td>
    </tr>
    <tr>
      <td>Turb. de Gas Natural</td>
      <td>gas </td>
    </tr>
    <tr>
      <td>Motores de CI</td>
      <td>oil </td>
    </tr>
    <tr>
      <td>Ing. Azucareros</td>
      <td>biomass </td>
    </tr>
    <tr>
      <td>GDR Térmico</td>
      <td>unknown </td>
    </tr>
  </tbody>
</table>

> **Note** GDR corresponds to the distributed generation capacity

&nbsp;</details>
&nbsp;<details><summary>HN</summary>

**Main link**: https://siehonduras.olade.org/WebForms/Reportes/VisorDocumentos.aspx?or=453&ss=7&v=1

**Search for**: Informe Estadístico Anual del Subsector Eléctrico

**Data table**: Tabla 1 – Potencia eléctrica instalada

**Mode mapping**:
<table>
  <thead>
    <tr>
      <th>Mode</th>
      <th>Electricity Maps mode</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>FÓSIL</td>
      <td>oil</td>
    </tr>
    <tr>
      <td>HIDROELÉCTRICA</td>
      <td>hydro </td>
    </tr>
    <tr>
      <td>SOLAR</td>
      <td>solar </td>
    </tr>
    <tr>
      <td>EÓLICAS</td>
      <td>wind </td>
    </tr>
    <tr>
      <td>BIOMASA</td>
      <td>biomass </td>
    </tr>
    <tr>
      <td>CARBÓN</td>
      <td>coal </td>
    </tr>
    <tr>
      <td>GEOTÉRMICA</td>
      <td>geothermal </td>
    </tr>
  </tbody>
</table>
&nbsp;</details>

## Technical requirements for adding a new data source <a name="#technical_requirements"></a>

If a new data source becomes available for a zone that does **not** have a capacity parser:

- **Verify the data source.** Please refer to our wiki page [Verify data sources](https://github.com/electricitymaps/electricitymaps-contrib/wiki/Verify-data-sources). The data should come from an authoritative data source, the criteria are listed on the wiki page.
- **Update this document with the new data source**. For maintainability and transparency reasons, the data should be easily accessible. This will enable another contributor to update the capacity breakdown in the future.
- **Add the guidelines to collect the data**. This should also be done for maintainability and transparency reasons.

If the capacity for the zone in question is collected using a capacity parser:

- **Verify the data source.**
- **Compare the new data with the existing data.** As explained above, we want to limit the number of data sources used and wish to use sources for which a certain level of quality is implied.
- **Discuss with the Electricity Maps team.** If the new data source is indeed of higher quality and meets all the requirements, feel free to ask the Electricity Maps team. We will find the best way forward otgether :)

