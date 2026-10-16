# ERCOT CRR Holder - Data

## Datasets

| Publication                                                                                                                         | Release                           |
|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| [CRR Ownership of Record: NP7-157-SG](https://www.ercot.com/mp/data-products/data-product-details?id=NP7-157-SG)                    | Monthly                           |
| [List of Market Participants: NP12-215-ER](https://www.ercot.com/mp/data-products/data-product-details?id=NP12-215-ER): tab `CRRAH` | Daily                             |
| [CRR CRR Time of Use Hours](https://www.ercot.com/files/docs/2021/04/16/CRR-Time-of-Use-Hours_2026-2029_UPD.xlsx)                   | Monthly? sync with CRR Ownership? |



* The Market Participants list is for enrichment, give context to the account
  holders - the main exploratory entity.

## CRR Ownership of Record

### Example Data

| CRR_ID    | SegmentID | AccountHolder | HedgeType | CRRType  | Source   | Sink       | StartDate  | EndDate    | TimeOfUse |  MW |
|-----------|-----------|---------------|-----------|----------|----------|------------|------------|------------|-----------|----:|
| 209146391 | 1         | XLUREP        | OBL       | STANDARD | HB_NORTH | LZ_NORTH   | 06/01/2027 | 06/30/2027 | PeakWE    | 974 |
| 214686172 | 1         | XLUREP        | OBL       | STANDARD | HB_NORTH | HB_HOUSTON | 08/01/2028 | 08/31/2028 | PeakWD    | 920 |
| 214686157 | 1         | XLUREP        | OBL       | STANDARD | HB_NORTH | HB_HOUSTON | 07/01/2028 | 07/31/2028 | PeakWD    | 900 |
| 186372993 | 1         | XLUREP        | OBL       | STANDARD | HB_NORTH | LZ_NORTH   | 12/01/2026 | 12/31/2026 | PeakWE    | 875 |
| 214683915 | 1         | XLUREP        | OBL       | STANDARD | HB_NORTH | HB_HOUSTON | 08/01/2028 | 08/31/2028 | PeakWE    | 857 |


* [CRR Market User Interface
  Handbook](https://www.ercot.com/files/docs/2019/05/07/CRR_Market_User_Interface_Handbook_v4.3.docx):
  section 2.5 "CRR Attribute definitions" contains column descriptions.


* `SegmentID`: decomposed blocks e.g. a strip broken into segments for
  "reasons"; NB: share the same `CRR_ID`; a key is really `(CRR_ID, segmentID)`

* `HedgeType`: `OPT`|`OBL`

* `CRRType`: mostly payment state differences; except for `REFUND` which is
  about when size gets resolved but I think we can ignore for now.

* `TimeofUse`: `PeakWD`, `PeakWE`, `Off-peak` blocks.


### Data Exploration


#### Account Holders

* ~530 account holders.
* just a table to join and decipher the AccountHolder
* Maybe aggregate on email domain, but also a corporate entity could have
  different interests with each sub-entity - trading vs running a gas peaker -
  so hold off on larger aggregation.


#### CRR Records

* Monthly release cadence
* ~ 757k records

* Range: 7/1/2026 - 12/31/2029 - so roughly 36 + 5/6 months -> 42 months to display
* Source, sinks: 1000 sources, 1000 sinks; 1M possible pairs, though only ~50k visible
  * then also possible option vs obligation, then time of use, combinations will explode
  -> motivates view; can't have 1M columns is unwieldy to view


* HedgeType: `OPT` are actually > 500k of the rows compared to `OBL`, so need to
  treat options as first class citizens


### Is there anything worth building?

`python -i explore.py`:

```text


Top 10 account holders by total MWh (OBL + OPT)
AccountHolder                                              name                 domain           MWh
       XLUREP          LUMINANT ENERGY COMPANY LLC REPS (CRRAH)         vistracorp.com 107,134,862.5
       XNRGLD                NRG TEXAS POWER LLC (LOAD) (CRRAH)                nrg.com  91,660,830.7
        XMEA1             MERCURIA ENERGY AMERICA LLC 1 (CRRAH)           mercuria.com  91,286,665.1
       XDARBY                          DARBY ENERGY LLC (CRRAH)                sig.com  76,169,154.6
       XEXELO       CONSTELLATION ENERGY GENERATION LLC (CRRAH)      constellation.com  70,935,119.3
        XCPSE                                CPS ENERGY (CRRAH)          cpsenergy.com  65,276,849.5
       XSHEL3      SHELL ENERGY NORTH AMERICA (US) LP 3 (CRRAH)              shell.com  52,423,520.6
        XLUMN               LUMINANT ENERGY COMPANY LLC (CRRAH)         vistracorp.com  44,424,790.4
       XSHEL2      SHELL ENERGY NORTH AMERICA (US) LP 2 (CRRAH)              shell.com  37,603,479.1
        XLCRA            LOWER COLORADO RIVER AUTHORITY (CRRAH)               lcra.org  36,675,760.6
         XMEA               MERCURIA ENERGY AMERICA LLC (CRRAH)           mercuria.com  36,112,572.9
         XAEN          CITY OF AUSTIN DBA AUSTIN ENERGY (CRRAH)       austinenergy.com  33,004,831.0
       XDCEN2                     DC ENERGY TEXAS LLC 2 (CRRAH)          dc-energy.com  32,588,148.8
        XNRGP                NRG BUSINESS MARKETING LLC (CRRAH)                nrg.com  30,602,870.8
        XSTEC      SOUTH TEXAS ELECTRIC COOPERATIVE INC (CRRAH)               stec.org  30,500,958.4
       XLUTRD       LUMINANT ENERGY COMPANY LLC TRADING (CRRAH)         vistracorp.com  30,224,747.9
       XDCEN3                     DC ENERGY TEXAS LLC 3 (CRRAH)          dc-energy.com  28,016,183.6
       XDYST1                       DYNASTY POWER INC 1 (CRRAH)        dynastypower.ca  27,964,422.3
       XDCENG                       DC ENERGY TEXAS LLC (CRRAH)          dc-energy.com  26,697,668.6
        XTENS                 TENASKA POWER SERVICES CO (CRRAH)               tnsk.com  25,406,991.5
       XPERAS                          PERAST TEXAS LLC (CRRAH)      perastcapital.com  24,757,007.5
       XECNRQ                      RWE AMERICAS QSE LLC (CRRAH)                rwe.com  24,416,745.0
       XCALPP              CALPINE POWER MANAGEMENT LLC (CRRAH)            calpine.com  24,289,153.6
       XDARB2                        DARBY ENERGY LLC 2 (CRRAH)                sig.com  23,520,679.1
         XDEN                       PENINSULA POWER LLC (CRRAH)          trafigura.com  22,635,447.9
       XEDIS2 BOSTON ENERGY TRADING AND MARKETING LLC 2 (CRRAH)               betm.com  21,442,057.9
        XBPEC                         BP ENERGY COMPANY (CRRAH)                 bp.com  20,760,068.7
       XUNCIA                  UNCIA ENERGY LP SERIES E (CRRAH)          trafigura.com  19,139,454.7
       XUNCI3                UNCIA ENERGY LP SERIES E 3 (CRRAH)          trafigura.com  18,457,865.8
       XTENS2               TENASKA POWER SERVICES CO 2 (CRRAH)               tnsk.com  17,994,501.6
       XRESI1               RESISTANCE ENERGY FUND LP 1 (CRRAH)          cwpenergy.com  17,946,047.4
       XUNCI2                UNCIA ENERGY LP SERIES E 2 (CRRAH)          trafigura.com  17,916,546.2
       XCALP2            CALPINE POWER MANAGEMENT LLC 2 (CRRAH)            calpine.com  17,726,901.8
       XDCEN1                    DC ENERGY DAKOTA LLC 1 (CRRAH)          dc-energy.com  17,467,970.8
       XBIOUR                RIVERCREST POWER SOUTH LLC (CRRAH)      61commodities.com  17,322,600.8
       XINTER                       INTERGRID POWER LLC (CRRAH)                mtu.edu  17,313,677.9
         XLQA                                   LQA LLC (CRRAH)               tnsk.com  16,832,444.0
        XGEXA                            GEXA ENERGY LP (CRRAH)                nee.com  16,773,750.1
       XDCND2                    DC ENERGY DAKOTA LLC 2 (CRRAH)          dc-energy.com  16,617,993.7
        XMEA2             MERCURIA ENERGY AMERICA LLC 2 (CRRAH)           mercuria.com  16,518,963.8
        XEAGL           EDF TRADING NORTH AMERICA LLC I (CRRAH)  edfenergyservices.com  16,498,663.4
       XSARA3                  SARACEN ENERGY WEST LP 3 (CRRAH)      saracenenergy.com  16,496,312.2
       XGUNVO                            GUNVOR USA LLC (CRRAH)        gunvorgroup.com  16,304,999.5
       XPERA1                        PERAST TEXAS LLC 1 (CRRAH)      perastcapital.com  16,260,554.3
       XTENS3               TENASKA POWER SERVICES CO 3 (CRRAH)               tnsk.com  16,249,800.6
        XMAGE                  MAG ENERGY SOLUTIONS INC (CRRAH) magenergysolutions.com  16,174,279.8
       XTXAP3        TX ACTIVE POWER INVESTMENTS LLLP 3 (CRRAH)            hotmail.com  15,952,340.0
       XGBPP2                            GBP POWER LP 2 (CRRAH)           gbppower.com  15,467,988.4
       XPEAKE                    PEAK ENERGY CAPITAL LP (CRRAH)      peakenergycap.com  15,457,400.1
       XBTGP2                  ENGELHART CTP (US) LLC 2 (CRRAH)               ectp.com  15,407,353.7

Top by domain
                domain           MWh
        vistracorp.com 181,784,400.8
          mercuria.com 143,918,201.8
         trafigura.com 133,975,422.8
         dc-energy.com 133,513,739.1
               nrg.com 127,336,615.4
              tnsk.com 104,495,648.2
               sig.com  99,690,505.7
             shell.com  90,026,999.7
     peakenergycap.com  83,056,260.5
         cpsenergy.com  72,916,883.1
     constellation.com  70,935,119.3
     perastcapital.com  52,475,965.5
               rwe.com  50,794,608.0
       dynastypower.ca  50,026,927.9
             vitol.com  47,596,669.3
               nee.com  45,705,124.6
              betm.com  45,584,034.2
           calpine.com  42,016,055.4
         cwpenergy.com  41,315,297.5
     saracenenergy.com  39,958,635.5
              lcra.org  36,676,752.6
          gbppower.com  34,516,128.0
      austinenergy.com  33,004,831.0
   hartreepartners.com  32,771,330.8
       soleaenergy.com  32,080,267.4
magenergysolutions.com  31,618,589.9
             engie.com  31,517,476.9
              stec.org  30,500,958.4
        atnvenergy.com  27,756,865.5
           hotmail.com  26,641,858.8
              ectp.com  26,427,347.8
     61commodities.com  26,400,620.0
           konapwr.com  24,739,122.9
   appianwayenergy.com  24,206,509.5
 edfenergyservices.com  24,044,722.8
                bp.com  23,422,893.3
    cascadetrading.com  23,397,472.7
               cci.com  23,139,682.4
          sescollc.com  23,085,298.0
        strompower.com  20,905,140.6
       altopenergy.com  20,661,983.3
             ecesis.ai  19,369,768.6
          plutuslp.com  18,574,755.2
           citadel.com  18,163,704.2
        bayespower.com  17,985,414.8
        durablepwr.com  17,800,335.0
               sumo.co  17,609,119.5
               mtu.edu  17,313,677.9
            pntfin.com  16,633,648.4
       gunvorgroup.com  16,304,999.5

Top 10 source/sink pairs by total MWh (OBL + OPT)
      Source        Sink           MWh
    HB_NORTH    LZ_NORTH 163,664,732.2
  HB_HOUSTON  LZ_HOUSTON 108,882,466.7
     HB_WEST     LZ_WEST  72,644,371.3
    HB_SOUTH    LZ_SOUTH  59,297,054.8
    HB_NORTH  HB_HOUSTON  46,527,360.4
    HB_NORTH     HB_WEST  25,624,949.4
    HB_NORTH    HB_SOUTH  16,294,760.3
CALAVER_JKS1      LZ_CPS  15,749,000.2
     HB_WEST    HB_NORTH  15,011,277.4
    HB_SOUTH    HB_NORTH  14,209,449.6
  HB_HOUSTON    HB_NORTH  13,911,836.0
        AEEC PALE_ESS_EN  12,978,616.5
  STP_STP_G1      LZ_CPS  10,719,196.0
  STP_STP_G2      LZ_CPS  10,613,228.4
FPPYD_FPP_G1      LZ_AEN   8,576,581.9
FPPYD_FPP_G2      LZ_AEN   8,566,018.3
BRA_AVR_CST1      LZ_CPS   8,466,213.7
FPPYD_FPP_G3     LZ_LCRA   8,325,031.6
 CPSES_UNIT1    HB_NORTH   8,227,072.9
BRISCOE_WIND      HB_PAN   8,002,796.2
FRNYPP_1_CCU    HB_NORTH   7,609,730.4
NED_NEDIN_G3    LZ_SOUTH   7,105,901.9
    TORR_ALL  CORAZON_RN   6,995,687.8
NED_NEDIN_G2    LZ_SOUTH   6,967,957.8
NED_NEDIN_G1    LZ_SOUTH   6,963,122.6
 CPSES_UNIT2    HB_NORTH   6,943,265.0
     OGSES_1    HB_NORTH   6,269,906.8
FRNYPP_2_CCU    HB_NORTH   6,219,536.9
    WHCCS2_4    HB_NORTH   6,215,003.5
   CBECII_89    HB_NORTH   6,183,738.8
  STP_STP_G1      LZ_AEN   6,019,678.7
  STP_STP_G2      LZ_AEN   5,959,076.7
    HB_SOUTH     LZ_LCRA   5,954,783.3
      HB_PAN     HB_WEST   5,950,986.4
FPPYD_FPP_G1     LZ_LCRA   5,707,560.6
 MLSES_UNIT1    HB_NORTH   5,683,814.4
FPPYD_FPP_G2     LZ_LCRA   5,650,857.1
SAN_SANMIGG1    LZ_SOUTH   5,639,733.1
  BORDAS_345   RELOJ_ALL   5,574,555.5
 VORT_ALL_RN    AZURE_RN   5,552,291.3
     PHO_ALL      MAG_RN   5,461,479.5
  LPCCS_CT12  LPCCS_CT11   5,368,634.2
JADE_SLR_ALL DERMOTT_ALL   5,259,766.1
     OGSES_2    HB_NORTH   5,150,027.1
  WHCCS2_5_6    HB_NORTH   4,959,263.2
  ANCHOR_ALL    HB_NORTH   4,815,896.5
  LPCCS_CT11  LPCCS_CT12   4,677,730.2
 HYDR_ESS_RN  WAYMARK_RN   4,594,898.2
    AZURE_RN GRIF_TRL_RN   4,580,755.8
  STP_STP_G2    HB_NORTH   4,522,382.0

Path breadth vs depth for the largest account holders (OBL + OPT)
AccountHolder                                              name     total_mwh  distinct_pairs  mwh_per_pair  top_5_pairs_share_pct
       XLUREP          LUMINANT ENERGY COMPANY LLC REPS (CRRAH) 107,134,862.5              15   7,142,324.2                   89.2
       XNRGLD                NRG TEXAS POWER LLC (LOAD) (CRRAH)  91,660,830.7               4  22,915,207.7                  100.0
        XMEA1             MERCURIA ENERGY AMERICA LLC 1 (CRRAH)  91,286,665.1            1915      47,669.3                   35.6
       XDARBY                          DARBY ENERGY LLC (CRRAH)  76,169,154.6             694     109,753.8                   10.7
       XEXELO       CONSTELLATION ENERGY GENERATION LLC (CRRAH)  70,935,119.3              30   2,364,504.0                   58.8
        XCPSE                                CPS ENERGY (CRRAH)  65,276,849.5              44   1,483,564.8                   75.6
       XSHEL3      SHELL ENERGY NORTH AMERICA (US) LP 3 (CRRAH)  52,423,520.6              31   1,691,081.3                   52.7
        XLUMN               LUMINANT ENERGY COMPANY LLC (CRRAH)  44,424,790.4             102     435,537.2                   71.2
       XSHEL2      SHELL ENERGY NORTH AMERICA (US) LP 2 (CRRAH)  37,603,479.1              28   1,342,981.4                   70.3
        XLCRA            LOWER COLORADO RIVER AUTHORITY (CRRAH)  36,675,760.6              29   1,264,681.4                   68.7
         XMEA               MERCURIA ENERGY AMERICA LLC (CRRAH)  36,112,572.9            1828      19,755.2                   10.5
         XAEN          CITY OF AUSTIN DBA AUSTIN ENERGY (CRRAH)  33,004,831.0              39     846,277.7                   94.7
       XDCEN2                     DC ENERGY TEXAS LLC 2 (CRRAH)  32,588,148.8            2254      14,457.9                    7.4
        XNRGP                NRG BUSINESS MARKETING LLC (CRRAH)  30,602,870.8              14   2,185,919.3                   55.6
        XSTEC      SOUTH TEXAS ELECTRIC COOPERATIVE INC (CRRAH)  30,500,958.4              14   2,178,639.9                   93.6
       XLUTRD       LUMINANT ENERGY COMPANY LLC TRADING (CRRAH)  30,224,747.9              91     332,140.1                   63.3
       XDCEN3                     DC ENERGY TEXAS LLC 3 (CRRAH)  28,016,183.6            2099      13,347.4                    7.0
       XDYST1                       DYNASTY POWER INC 1 (CRRAH)  27,964,422.3            1881      14,866.8                   18.2
       XDCENG                       DC ENERGY TEXAS LLC (CRRAH)  26,697,668.6            2134      12,510.6                    6.3
        XTENS                 TENASKA POWER SERVICES CO (CRRAH)  25,406,991.5             717      35,435.1                   13.7
       XPERAS                          PERAST TEXAS LLC (CRRAH)  24,757,007.5            3390       7,303.0                    6.1
       XECNRQ                      RWE AMERICAS QSE LLC (CRRAH)  24,416,745.0             184     132,699.7                   29.0
       XCALPP              CALPINE POWER MANAGEMENT LLC (CRRAH)  24,289,153.6              51     476,257.9                   37.7
       XDARB2                        DARBY ENERGY LLC 2 (CRRAH)  23,520,679.1             958      24,551.9                    9.3
         XDEN                       PENINSULA POWER LLC (CRRAH)  22,635,447.9              65     348,237.7                   66.5
       XEDIS2 BOSTON ENERGY TRADING AND MARKETING LLC 2 (CRRAH)  21,442,057.9            5148       4,165.1                    1.2
        XBPEC                         BP ENERGY COMPANY (CRRAH)  20,760,068.7             706      29,405.2                   55.6
       XUNCIA                  UNCIA ENERGY LP SERIES E (CRRAH)  19,139,454.7            1978       9,676.2                   10.7
       XUNCI3                UNCIA ENERGY LP SERIES E 3 (CRRAH)  18,457,865.8            1995       9,252.1                   10.3
       XTENS2               TENASKA POWER SERVICES CO 2 (CRRAH)  17,994,501.6             534      33,697.6                    7.4
       XRESI1               RESISTANCE ENERGY FUND LP 1 (CRRAH)  17,946,047.4            3233       5,550.9                    9.0
       XUNCI2                UNCIA ENERGY LP SERIES E 2 (CRRAH)  17,916,546.2            2023       8,856.4                   10.2
       XCALP2            CALPINE POWER MANAGEMENT LLC 2 (CRRAH)  17,726,901.8              65     272,721.6                   41.9
       XDCEN1                    DC ENERGY DAKOTA LLC 1 (CRRAH)  17,467,970.8            3656       4,777.9                    3.4
       XBIOUR                RIVERCREST POWER SOUTH LLC (CRRAH)  17,322,600.8            2943       5,886.0                    2.5
       XINTER                       INTERGRID POWER LLC (CRRAH)  17,313,677.9            2524       6,859.6                    9.6
         XLQA                                   LQA LLC (CRRAH)  16,832,444.0             576      29,223.0                    4.8
        XGEXA                            GEXA ENERGY LP (CRRAH)  16,773,750.1               4   4,193,437.5                  100.0
       XDCND2                    DC ENERGY DAKOTA LLC 2 (CRRAH)  16,617,993.7            3446       4,822.4                    3.2
        XMEA2             MERCURIA ENERGY AMERICA LLC 2 (CRRAH)  16,518,963.8            2510       6,581.3                    4.2
        XEAGL           EDF TRADING NORTH AMERICA LLC I (CRRAH)  16,498,663.4              25     659,946.5                   77.1
       XSARA3                  SARACEN ENERGY WEST LP 3 (CRRAH)  16,496,312.2            1449      11,384.6                    4.5
       XGUNVO                            GUNVOR USA LLC (CRRAH)  16,304,999.5             177      92,118.6                   14.6
       XPERA1                        PERAST TEXAS LLC 1 (CRRAH)  16,260,554.3            2799       5,809.4                    6.1
       XTENS3               TENASKA POWER SERVICES CO 3 (CRRAH)  16,249,800.6             597      27,219.1                    9.4
        XMAGE                  MAG ENERGY SOLUTIONS INC (CRRAH)  16,174,279.8            1822       8,877.2                    7.1
       XTXAP3        TX ACTIVE POWER INVESTMENTS LLLP 3 (CRRAH)  15,952,340.0             755      21,128.9                   14.8
       XGBPP2                            GBP POWER LP 2 (CRRAH)  15,467,988.4             126     122,761.8                   38.6
       XPEAKE                    PEAK ENERGY CAPITAL LP (CRRAH)  15,457,400.1            3767       4,103.4                    3.6
       XBTGP2                  ENGELHART CTP (US) LLC 2 (CRRAH)  15,407,353.7             145     106,257.6                   37.8

```


The last breadth vs depth is interesting: `GEXA ENERGY LP` and `NRG TEXAS POWER
LLC (LOAD)` have CRRs on only 4 distinct pairs - the NRG entity has significant
MWh size - all of its CRRs are on 4 pairs, compared to say `DC ENERGY DAKOA`,
whose total CRR size is distributed on many pairs in much smaller size,
indicating broad but smaller CRR participation.

This suggests there are distinct profiles per entity, and there's probably a
worthwhile project looking into this: what are the positions / holdings; what
particular source/sink pairs, what time frame, TOU, what percentage of
generation is already hedged out?



---


## Ingest

1. utility to calculate TOU hours (month -> peak/offpeak hours)
2. topology.json with lat/lng coords
3. import parse excel sheets - fetch and reliable excel ingestion
  * add report_id for monthly persistence


### TOU Ingest

* TOU (peak vs offpeak) and MWh as the aggregate values

* since CRR are monthly we can just have small table ( peak hours, offpeak, etc
  x month ) top get hours. Trick is holidays.

* then on join we calc total mwH
* alternative is a frontend "conversion", maybe submit each total as Peak/OFfPeak object?

or return an object

type MWByTOU = {
  peakWD: number;
  peakWE: number;
  offPeak: number;
};

type MWhByTOU = {
  peakWD: number;
  peakWE: number;
  offPeak: number;
};


and then a TOU table
{
  "2026-10": {
    "peakWD": 0,
    "peakWE": 0,
    "offPeak": 0
  },
  "2026-11": {
    "peakWD": 0,
    "peakWE": 0,
    "offPeak": 0
  }
}


### Materialized Table

* crr_holdings: raw ERCOT record
* account_holders: ERCOT entity directory

* materialize -> crr_monthly_holdings

If this is our aggregate query:

```sql

SELECT
    source,
    sink,
    delivery_month,
    hedge_type,
    SUM(peak_wd_mw) AS peak_wd,
    SUM(peak_we_mw) AS peak_we,
    SUM(off_peak_mw) AS off_peak
FROM crr_monthly_holdings
WHERE account_holder = ?
GROUP BY source, sink, delivery_month, hedge_type;
```


we have our original records:

```text
| CRR ID | Account | Source | Sink | Start    | End      | TOU      |  MW |
|--------|---------|--------|------|----------|----------|----------|----:|
| 101    | XMEA1   | A      | B    | Oct 2026 | Dec 2026 | PeakWD   | 100 |
| 102    | XMEA1   | A      | B    | Nov 2026 | Dec 2026 | PeakWD   |  50 |
| 103    | XMEA1   | A      | B    | Oct 2026 | Nov 2026 | Off-peak |  75 |
```

* need to break strips into months

```text
| CRR ID | Month | TOU      |  MW |
|--------|-------|----------|----:|
| 101    | Oct   | PeakWD   | 100 |
| 101    | Nov   | PeakWD   | 100 |
| 101    | Dec   | PeakWD   | 100 |
| 102    | Nov   | PeakWD   |  50 |
| 102    | Dec   | PeakWD   |  50 |
| 103    | Oct   | Off-peak |  75 |
| 103    | Nov   | Off-peak |  75 |
```

* now we can aggregate into shape of our results

```text
| Account | Source | Sink | Month | Hedge | PeakWD MW | PeakWE MW | Off-peak MW |
|---------|--------|------|-------|-------|----------:|----------:|------------:|
| XMEA1   | A      | B    | Oct   | OPT   |       100 |         0 |          75 |
| XMEA1   | A      | B    | Nov   | OPT   |       150 |         0 |          75 |
| XMEA1   | A      | B    | Dec   | OPT   |       150 |         0 |           0 |
```
