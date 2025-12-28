### quiz_maps

Site to show pub quiz days and ratings around Manchester.

For each quiz, show
* Day of the week/month
* Average rating (overall)
* Average rating (by rater)
* Location

User should be able to submit rating to a Google Form. Google Form saves to Google Sheet, which aggregates all submissions by location and by location + rater.

How to keep ratings relative? For example, if on week 10, pub quiz A is the best one I've been to and then on week 20, I go to one at pub B that's even better, pub quiz B should have a higher rating than pub quiz A.

Method:
* Pick a random quiz (1) that has already been visited by user
* Ask if the new quiz was better or worse than that
* Find one that was better/worse rated already than quiz 1
* Ask if the new quiz was better or worse than that
* Repeat up to 3 times for placement.
* Do not use each visit as a separate one to ask about, but ask if it was better/worse than the previous visit to the same place if repeated. This will allow a quiz to be re-rated by recency. Store the rating of that quiz after each visit.

NOTE: start with a single user (me!)
TODO: keep API keys as secrets (Python worker in Cloudflare)
TODO: remove public folder from worker and instead upload index.html to suriya.io pages?

DB Schema:
Pub
- ID
- Name
- Location
- Day of the Week
- Frequency
- Rating

Visit
- ID
- Pub ID
- Date
- Lower bound rating Pub ID (nullable)
- Upper bound rating Pub ID (nullable)

Comparison
- Visit ID
- Other pub ID
- Better (0 if visit pub is better, 1 if other pub is better)

