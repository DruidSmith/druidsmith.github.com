---
published: false
---

## Challenges in Government Data

_These are some follow-on thoughts to a session titled "Getting Value out of Government Data", with perspectives from a data wrangler who's now a recently minted  govie coming in from the private sector_

### This is not intended as a full recap of all presentations, but instead just highlight some items of particular interest to me relating to government data transparency and usability:

- Josh Hurd [@nonprofmetrics](http://twitter.com/nonprofmetrics) gave a presentation on mining government data for use in analysis of non-profits and discussed some of the challenges of using the data, for example that IRS provides scanned TIFF image, which need to be processed into being machine-readable, and which then still contain many errors and other data quality problems.  They actually have been looking at committing a full time hire just to deal with the data quality issues

- Hudson Hollister [@hudsonhollister](http://twitter.com/hudsonhollister) gave a presentation on data transparency and hit the nail on its head in citing an example from his own experience at SEC of a very document and process focused culture in government, as opposed to an information and business process focused culture  He also mentioned that government is not likely to take the time to develop machine-readable regulatory information. [Data Transparency Coalition](http://datacoalition.org/) 

- Aneet Makin [@legcyte](http://twitter.com/legcyte) discussed opening up legislative data via [LegCyte](http://www.legcyte.com/), along with being able to recognize language from prior bills and track the originating legislator.

- Tom Lee [@sunlightlabs](http://twitter.com/sunlightlabs) made a great case for the value of government data and gave several examples, i.e. MapBox, Zonability, and Brightscope, where it falls in the category of "public good" - and of the business case of dealing with government data that is non-rivalrous and non-excludable.  However, he likewise reiterated the data quality problems and underscored some of the previous themes.

### My thoughts and perspectives on how government should reform how it deals with data:

- The primary issue of government data transparency is not so much getting good data out of the government - it's in getting good data INTO the government.  The IRS and SEC example cited by Hurd and Hollister were perfect illustrations of bad business process and continued overreliance on paper forms.

- The biggest issue in government is that not enough thought is given up front regarding data collection.  It is far more costly and unreliable to try and QA and work with bad data after the fact than it is to make an up-front investment in collecting good data in the first place.

- Government agencies should, by default, be making all new information flows electronic and web-enabled. Tthat does not mean downloading a PDF to fill out and submit.  Paper forms could be a fall-back position only for demonstrated cases where a submitter for whatever reason absolutely cannot submit electronically - and then, there should still be a process whereby the data would still be entered into the same system on receipt, whether by OCR or manually.

- Toward burden reduction, governmental agencies should minimize repetetive entry of information, in a "TurboTax" type approach.  That means, retrieving already-known, previously-submitted information and prepopulating a form with it.  For example, an environmental health and safety official reporting for industry could enter the name of their company, "Spacely Sprockets" and location "Orbit City" and the reporting interface would call a web service to find potential matches, which the submitter could select from and it would prepopulate relevant sections of the form with known information.  The submitter could still submit updates or changes, but would have some basic pieces of their reporting burden reduced.  Similar lookups should be provided wherever possible - for example, if they are discharging industrial wastewater for treatment, a web service should be used to provide a picklist of nearby wastewater treatment plants - or if they are transporting oil or hazardous materials, they should be able to select from prepopulated picklists wherever possible, rather than being presented free-text fields to enter information.  This basic approach of lookups can and should be driven by enterprise web services wherever possible - and in many cases, shared, cross-governmental web services - for example standard data elements like NAICS codes should be driven by a web service, where for example the user could start typing "Petroleum" and the reporting interface would provide something like an AJAX drop-down listing or autocomplete that lists all of the relevant NAICS codes containing or dealing with petroleum and related concepts (potentially via ontology model)

- Toward cleaner and richer data, governmental agencies should use web services and smarter forms to improve data entry.  For example, if a street address is entered, the web form should call a geocoding web service to check if it's a valid address.  It could also provide a pop-up aerial photo map for visual verification.

- There should be no such thing as math errors or carry-over, i.e. "subtract line j from line m to get gross income" - these calculations should be done automatically, showing the result

- There should be a way to submit errors - for example if the web services do not return correct results, or there are other problems, those should be routed to agency stewards for review and tracking.

- The components for these reporting interfaces, lookups, validations, APIs, workflows and other tools should be documented, published, and shared as open source wherever possible, i.e. via [GitHub](http://github.com) - governmental tools are taxpayer-funded investments which should be shared.

- In cases where there are third party organizations working with government data, and they are identifying problems and issues, or are investing their own energy and resources into data cleanup, there should be a means of public-private stewardship, whereby a process would exist for reconciling externally identified data quality problems with the agency data.

- There are also some areas governmental agencies have data that they know to be incorrect, but cannot change it.  These may include systems where it is a system of legal record, and what was entered by the submitter can only be changed by the submitter, or where the data is being retrieved from another agency, and the change must happen at the source.  In these cases, there should likewise be a feedback mechanism - for example, notifying the submitter of the issue for resolution, or having interagency partnerships that include stewardship and have mechanisms for easily maintaining and exchanging human and machine readable data stewards lists, along with information flows that could send suggested changes to partner agencies.