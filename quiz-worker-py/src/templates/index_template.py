from datetime import datetime
from pyodide.ffi import JsNull

def INDEX_TEMPLATE(
    logged_in_user_id,
    all_pubs,
    pub_ranking,
    upcoming_events,
    geoapify_key=None
):
    # TODO: links to focus on pin from event
    # TODO: pin colors based on days

    all_pubs_dict = {
        pub.id: pub.name
        for pub in all_pubs
    }

    pan_a_tag = lambda pub_id, content: f'<a class="pantag" href="#" onclick="focusPin({pub_id})">{content}</a>'

    leaderboard_cells = '\n'.join([
        f"""
        <tr>
            <td>{i+1}</td>
            <td>{pan_a_tag(pub_id, all_pubs_dict[pub_id])}</td>
        </tr>
        """
        for i, pub_id in enumerate(pub_ranking)
    ])

    unranked_pub_ids = set([pub.id for pub in all_pubs]) - set(pub_ranking)
    unranked_cells = '\n'.join([
        f"""
        <tr>
            <td>-</td>
            <td>{pan_a_tag(pub_id, all_pubs_dict[pub_id])}</td>
        </tr>
        """
        for pub_id in unranked_pub_ids
    ])

    event_list_items = '\n'.join([
        """
        <li>{} - {} @ {}</li>
        """.format(
            event_dt.strftime("%A, %B %d"),
            pan_a_tag(pub.id, pub.name),
            event_dt.strftime("%I:%M %p")
        )
    for pub, event_dt in upcoming_events])

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    week_ordinals = ["", "1st", "2nd", "3rd", "4th"]

    def get_js_weeks_of_month_str(pub):
        weeks_of_month = [
            week_ordinals[int(wom)]
            for wom in (
                [] if type(pub.weeks_of_month) == JsNull or pub.weeks_of_month == '' else pub.weeks_of_month.split(',')
            )
        ]
        weeks_of_month_str = ""
        if len(weeks_of_month) > 1:
            weeks_of_month_str = ', '.join(weeks_of_month[:-1])
            sep_comma = ',' if len(weeks_of_month) > 2 else ''
            weeks_of_month_str = f"{weeks_of_month_str}{sep_comma} and {weeks_of_month[-1]}"
        elif len(weeks_of_month) == 1:
            weeks_of_month_str = weeks_of_month[0]

        return weeks_of_month_str

    locations = '\n'.join([
        f"""
        {{
            id: {pub.id},
            name: "{pub.name}",
            address: "{pub.address}",
            lat: {pub.lat},
            lng: {pub.lng},
            time: "{datetime.strptime(pub.time, "%H:%M").strftime("%I:%M%p")}",
            frequency: "{pub.frequency}",
            day_of_week: "{days_of_week[pub.day_of_week]}",
            weeks_of_month: "{get_js_weeks_of_month_str(pub)}"
        }},
        """
        for pub in all_pubs
    ])

    login_href = '/profile' if logged_in_user_id is not None else '/login'
    login_icon = '🌞' if logged_in_user_id is not None else '🌚'

    add_pub_to_db = ""
    if logged_in_user_id is not None:
        add_pub_to_db = f"""
        // Geoapify for geocoding
        const geoapifyApiKey = "{geoapify_key}";

        // Function to add location to database
        async function addToDatabase(place_id, address, timezone, lat, lng) {{
            // TODO: prevent double-submit
            const formId = `form-${{place_id}}`;
            const form = document.getElementById(formId);
            const formData = new FormData(form);

            const scheduleData = {{
                place_id: place_id,
                name: formData.get('name'),
                address: address,
                frequency: formData.get('frequency'),
                dayOfWeek: formData.get('dayOfWeek'),
                weeksOfMonth: formData.getAll('weekOfMonth'),
                time: formData.get('time'),
                timezone: timezone,
                lat: lat,
                lng: lng
            }};

            // Send POST request
            const response = await fetch('/api/pub', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify(scheduleData)
            }});

            // TODO: instead of reloading, remove popup, add location to pins, and re-zoom map
            window.location.reload();
        }}

        function updateFormFields(formId) {{
            const form = document.getElementById(formId);
            const frequency = form.querySelector('[name="frequency"]').value;
            const weekOfMonthGroup = form.querySelector('.week-of-month-group');

            if (frequency === 'specific-weeks') {{
                weekOfMonthGroup.style.display = 'block';
            }} else {{
                weekOfMonthGroup.style.display = 'none';
            }}
        }}

        // Add Geoapify Address Search control
        const addressSearchControl = L.control.addressSearch(geoapifyApiKey, {{
          position: 'topleft',
          resultCallback: (loc) => {{
            map.setView([loc.lat, loc.lon], 25);

            const formId = `form-${{loc.place_id}}`;

            const loc_name = loc.name === undefined ? '' : loc.name;

            // TODO: fill form with existing info and update button if quiz already exists
            const popupContent = `
                <div>
                    <!--<strong>${{loc.name}}</strong><br>-->
                    ${{loc.formatted}}<br><br>

                    <form id="${{formId}}">
                        <label>Name:</label><br>
                        <input
                            type="text" name="name" value="${{loc_name}}"
                            required placeholder="Enter name"
                            oninvalid="this.setCustomValidity('Enter pub quiz name here')"
                            oninput="this.setCustomValidity('')"
                            style="width: 100%; margin-bottom: 10px;"
                        ><br>

                        <label>Frequency:</label><br>
                        <select name="frequency" onchange="updateFormFields('${{formId}}')" style="width: 100%; margin-bottom: 10px;">
                            <option value="weekly">Every week</option>
                            <option value="specific-weeks">Specific weeks of month</option>
                        </select><br>

                        <div class="week-of-month-group" style="display: none; margin-bottom: 10px;">
                            <label>Week(s) of month:</label><br>
                            <label><input type="checkbox" name="weekOfMonth" value="1"> 1st</label>
                            <label><input type="checkbox" name="weekOfMonth" value="2"> 2nd</label>
                            <label><input type="checkbox" name="weekOfMonth" value="3"> 3rd</label>
                            <label><input type="checkbox" name="weekOfMonth" value="4"> 4th</label><br>
                        </div>

                        <label>Day of week:</label><br>
                        <select name="dayOfWeek" style="width: 100%; margin-bottom: 10px;">
                            <option value="0">Monday</option>
                            <option value="1">Tuesday</option>
                            <option value="2">Wednesday</option>
                            <option value="3">Thursday</option>
                            <option value="4">Friday</option>
                            <option value="5">Saturday</option>
                            <option value="6">Sunday</option>
                        </select><br>

                        <label>Time:</label><br>
                        <input type="time" name="time" value="19:00" style="width: 100%; margin-bottom: 10px;"><br>

                        <button type="button" onclick="addToDatabase('${{loc.place_id}}', '${{loc.formatted}}', '${{loc.timezone.name}}', ${{loc.lat}}, ${{loc.lon}})">Add to Database</button>
                    </form>
                </div>
            `;

            L.marker([loc.lat, loc.lon])
                .addTo(map)
                .bindPopup(popupContent)
                .openPopup();

            // TODO: delete popup on search new location or add to database or cancel (TODO add to popup)
          }},
          suggestionsCallback: (suggestions) => {{
            // console.log(suggestions);
          }}
        }});
        map.addControl(addressSearchControl);
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Location Map</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/@geoapify/leaflet-address-search-plugin@^1/dist/L.Control.GeoapifyAddressSearch.min.css" />
        <script src="https://unpkg.com/@geoapify/leaflet-address-search-plugin@^1/dist/L.Control.GeoapifyAddressSearch.min.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet-search@3.0.9/dist/leaflet-search.min.css" />
        <script src="https://unpkg.com/leaflet-search@3.0.9/dist/leaflet-search.min.js"></script>
        <style>
          .circle-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: solid;
            border-color: #000000;
            background-color: #ffffff;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s;
          }}

          .circle-btn:hover {{
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
          }}

          .circle-btn:active {{
            transform: scale(0.95);
          }}

          a.pantag:link {{
            color:blue
          }}

          a.pantag:visited {{
            color: blue;
          }}
        </style>
    </head>
    <body>
        <div style="display: flex; height: 100vh; margin: 0;">
            <div style="flex: 1;">
                <div id="map" style="width: 100%; height: 100%;"></div>
            </div>

            <div style="flex: 1; padding: 20px; overflow-y: auto;">
                <div style="margin-bottom: 40px;">
                    <h2>Upcoming Events (Next 7 Days)</h2>
                    <ul id="events-list">
                        {event_list_items}
                    </ul>
                </div>

                <div>
                    <h2>Best Quiz Ranking</h2>
                    <table border="1" cellpadding="8" cellspacing="0">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Name</th>
                            </tr>
                        </thead>
                        <tbody>
                            {leaderboard_cells}
                            {unranked_cells}
                        </tbody>
                    </table>
                </div>
            </div>
            <button class="circle-btn" onclick="window.location.href='{login_href}';">{login_icon}</button>
        </div>

        <script>
            // Pub locations
            const locations = [
                {locations}
            ];

            // Initialize the map to Manchester
            const map = L.map('map', {{zoomControl: false}}).setView([53.483959, -2.244644], 14);

            // If enough locations, fit map bounds to locations
            if (locations.length >= 2) {{
                const lats = locations.map(loc => loc.lat);
                const lngs = locations.map(loc => loc.lng);
                map.fitBounds([
                    [Math.min(...lats), Math.min(...lngs)],
                    [Math.max(...lats), Math.max(...lngs)]
                ]);
            }}

            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            // Add markers to the map
            var markerLayer = L.layerGroup().addTo(map);
            var placeIdMap = new Map();
            locations.forEach(loc => {{
                var freq = loc.frequency == 'weekly' ? `${{loc.day_of_week}}s` : `the ${{loc.weeks_of_month}} ${{loc.day_of_week}} of the month`

                var marker = L.marker([loc.lat, loc.lng], {{title: loc.name}})
                    .addTo(map)
                    .bindPopup(`
                        <h4>${{loc.name}}</h4>
                        <p>${{loc.address}}</p>
                        <p>${{loc.time}} on ${{freq}}</p>
                    `);
                var ret = markerLayer.addLayer(marker);

                placeIdMap.set(loc.id, marker._leaflet_id);
            }});

            {add_pub_to_db}

            map.addControl(new L.Control.Search({{
                initial: false,
                layer: markerLayer,
                autoType: false,
                marker: false,
                moveToLocation: (ll, t, m) => {{ll.layer.openPopup()}}
            }}));

            L.control.zoom({{ position: 'bottomright' }}).addTo(map);

            // Focus pin
            function focusPin(placeId) {{
                var marker = map._layers[placeIdMap.get(placeId)];
                map.panTo(marker._latlng);
                marker.openPopup();
            }}
        </script>
    </body>
    </html>
    """

