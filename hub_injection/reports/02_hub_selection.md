# Hub selection

Original edges only. Total degree = in + out; a self-loop counts twice. Parallel relations count separately. Ties use lexical QID order. Eligible = true boolean, valid general type, no quality flags, positive total degree.

Initial K = min(n, top_k_max, max(2, ceil(0.05*n))) for n >= 2; otherwise 0. Expansion doubles ranked prefixes deterministically, beyond the initial soft cap if needed.

| Type | Eligible positive-degree nodes | Selected K |
|---|---:|---:|
| AdministrativeArea | 339 | 17 |
| Brand | 2 | 2 |
| Building | 25 | 2 |
| CentralBank | 6 | 2 |
| CityTown | 583 | 20 |
| Company | 140 | 7 |
| Concept | 2 | 2 |
| Country | 73 | 4 |
| CreativeWork | 4 | 2 |
| CulturalInstitution | 14 | 2 |
| CulturalOrganization | 5 | 2 |
| EducationalInstitution | 76 | 4 |
| Event | 1 | 0 |
| Facility | 7 | 2 |
| Family | 1 | 0 |
| GeographicLocation | 2 | 2 |
| GovernmentOrganization | 83 | 5 |
| HigherEducationInstitution | 102 | 6 |
| MediaOrganization | 49 | 3 |
| Occupation | 1 | 0 |
| Organization | 122 | 7 |
| Person | 3719 | 20 |
| PoliticalParty | 167 | 9 |
| Position | 227 | 12 |
| ReligiousOrganization | 5 | 2 |
| ResearchInstitution | 34 | 2 |
| Road | 2 | 2 |
| School | 163 | 9 |
| ScientificInstrument | 1 | 0 |
| SportsOrganization | 39 | 2 |
| SportsTeam | 807 | 20 |
| SportsVenue | 338 | 17 |
| University | 506 | 20 |
| Vehicle | 1 | 0 |

The hub CSV contains all eligible positive-degree ranked nodes; selected_top_k identifies actual hubs. Full expansion attempts are in injection_manifest.json.
