Terminology
===========

Certain abbreviations, acronyms and terminology
are commonly used in QE-Tools and the QE org in general.

============  ========================  ============================================================
Abbreviation  Stands For                Definition
============  ========================  ============================================================
BRB           Be Right Back             |
DAMP          Descriptive and           | Give variables, classes, functions meaningful
              Meaningful Phrases        | names. Terse is good, but readable is better.
                                        | Applies to both test code and to Gherkin source.
                                        | DAMP is about readability, not an excuse to violate DRY.
DNCOF         Do Not Code On Fridays    | A phrase used in jest when you realize you made a
                                        | silly mistake on a Friday. Can be adapted to your
                                        | needs: DNCOM (Do Not Code On Monday), DNCDL
                                        | (Do Not Code During Lunch), and the likes.
DNM           Do Not Merge              | A PR that should not be merged (e.g., may break
                                        | functionality, opened for debugging or discussion)
DRY           Don't Repeat Yourself     | Most often used when code is cut'n'paste or otherwise
                                        | copied around: "DRY up the code" - remove the
                                        | duplication with a common helper, class, etc.
EB            Ear Burn                  | Request someones attention with a ping usually
                                        | via Slack or Github.
E>I           Explicit > Implicit       | Being explicit, even when stating the obvious is better
                                        | than implying or assuming.
FF            Fast Follow               | A fast follow for a previous PR (usually small, very
                                        | specific changes, expected to be completed quickly
                                        | after the PR merges).
FRFM          First Review First Merge  | A PR that can be merged by one and only one
                                        | reviewer. Usually a very small PR, that includes
                                        | only non-debatable changes. (examples might be
                                        | version bump PRs, typo fixes, doc string
                                        | standardization).
IIRC          If I Remember Correctly
LGTM          Looks Good To Me
NB            Non Blocking              | A PR comment that does not require changes.
PIR           Price Is Right            | One way to express a version dependency of >= X.
                                        | Based on the old game show of the same name.
                                        | Used in the context of "Test T has a PIR of Y",
                                        | meaning Test T is only valid for version Y, or greater,
                                        | of the system under test.
PR            Pull Request              | An official request to merge code into a repository
RR            Reserve the Right         | We Reserve the Right to get smarter and change things at
                                        | a later date if needed.
TIL           Today I Learned
WF            Will Fix
WFH           Work From Home
YAGNI         You Ain't Gonna Need It   | Something that might be a good idea but seems unlikely
                                        | to be used or needed.
============  ========================  ============================================================
