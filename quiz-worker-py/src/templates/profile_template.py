def PROFILE_TEMPLATE(
    user_visits,
    all_pubs,
    incomplete_comparisons,
):
    visit_list_items = '\n<br>\n'.join([
        """
        <div>
            {} <strong>{}</strong>
        </div>
        """.format(
            visit.date,
            visit.name,
        )
    for visit in sorted(user_visits, key=lambda p: p.date)[::-1]])

    pub_options = '\n'.join([
        f'<option value={pub.id}>{pub.name}</option>'
        for pub in sorted(all_pubs, key=lambda p: p.name)
    ])

    incomplete_comparison_list = '[' + ','.join([
        f'''{{
            id: {comparison.id},
            pub_name: "{comparison.pub_name}",
            compare_pub_id: {comparison.compare_pub_id},
            visit_date: "{comparison.date}",
            "better": "{comparison.better}"
        }}'''
        for comparison in incomplete_comparisons
    ]) + ']'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Visits Tracker</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css" rel="stylesheet" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js"></script>

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
        </style>
    </head>
    <body>
        <h1>Visits Tracker</h1>

        <table width="100%">
            <tr valign="top">
                <!-- Left side: List of visits -->
                <td width="50%">
                    <h2>Recent Visits</h2>
                    <div id="visitsList">
                        {visit_list_items}
                    </div>
                </td>

                <!-- Right side: Forms -->
                <td width="50%">
                    <div id="incompleteComparisonInfo">
                    </div>

                    <!-- New Visit Form -->
                    <h2>Add New Visit</h2>
                    <div id="newVisitInfo">
                        <form id="newVisitForm">
                            <div id="errorMessage" style="color: red; display: none;"></div>
                            <br>
                            <label for="location">Location:</label><br>
                            <select id="location" name="location" style="width: 300px;" required>
                                <option value="">-- Select a location --</option>
                                {pub_options}
                            </select>
                            <br><br>

                            <label for="date">Date:</label><br>
                            <input type="date" id="date" name="date" required>
                            <br><br>

                            <button type="submit">Add Visit</button>
                        </form>
                    </div>

                    <br><br>

                    <!-- Comparison Form -->
                    <div id="newComparisonInfo">
                    </div>
                </td>
            </tr>
        </table>

        <button class="circle-btn" onclick="window.location.href='/';">🗺️</button>

        <script>
            // Handle new visit form submission
            async function createNewComparisonForm(comparison, locationName) {{
                expectedComparisonIds.add(comparison.id)

                const comparePub = (await (await fetch(`/api/pub?id=${{comparison.compare_pub_id}}`, {{
                    method: 'GET',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }})).json())[0];

                return comparisonForm = `
                    <form id="comparisonForm_${{comparison.id}}" class="comparisonForm">
                        <input type="radio" name="better_${{comparison.id}}" id="visit_pub" value="1">
                        <label for="visit_pub">${{locationName}}</label>
                        <br><br>

                        <input type="radio" name="better_${{comparison.id}}" id="compare_pub" value="0">
                        <label for="compare_pub">${{comparePub.name}}</label>
                        <br><br>

                        <button type="button" onclick="submitComparisonForm(${{comparison.id}})">Submit Choice</button>
                    </form>
                    <br>
                `;
            }}

            $(document).ready(async function() {{
                // Initialize Select2
                $('#location').select2({{
                    placeholder: "Select a location",
                    allowClear: true
                }});

                // Create incomplete comparison forms
                const incompleteComparisons = {incomplete_comparison_list}
                var incompleteComparisonFormContent = incompleteComparisons.length > 0 ? '<h2>Pending Comparisons</h2>' : '';
                for (var i=0; i < incompleteComparisons.length; i++) {{
                    const comparison = incompleteComparisons[i];
                    const comparisonForm = await createNewComparisonForm(comparison, comparison.pub_name);
                    incompleteComparisonFormContent = `
                    ${{incompleteComparisonFormContent}}
                    <p><strong>Visit to ${{comparison.pub_name}} on ${{comparison.visit_date}}</strong></p>
                    ${{comparisonForm}}
                    `
                }}
                document.getElementById('incompleteComparisonInfo').innerHTML = incompleteComparisonFormContent;
            }});

            // Set default date to today
            document.getElementById('date').valueAsDate = new Date();

            var completedComparisonIds = new Set([]);
            var expectedComparisonIds = new Set([]);
            document.getElementById('newVisitForm').addEventListener('submit', async function(e) {{
                e.preventDefault();

                const locationId = document.getElementById('location').value;
                const locationName = $('#location option:selected').text();
                const errorMessage = document.getElementById('errorMessage');

                // Check if location is selected
                if (!locationId) {{
                    errorMessage.textContent = 'Please select a location from the list';
                    errorMessage.style.display = 'block';
                    return;
                }}

                // Hide error message if validation passes
                errorMessage.style.display = 'none';

                const date = document.getElementById('date').value;

                // Format the date
                const dateString = new Date(date).toISOString().substring(0,10);

                const visitData = {{
                    pub_id: locationId,
                    date: dateString
                }}

                // Post visit and get comparisons in response
                const visitResponse = await fetch('/api/visit', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(visitData)
                }});
                const visitResult = await visitResponse.json();

                // TODO: get pub name from location list passed in at beginning (turn it into a map). Make sure that a visit was actually returned.
                // const locationName = visitResult['visit']['id'];

                // TODO: visitDate should only be in the past (including today)
                const visitDate = visitResult['visit']['date']

                // Replace form with visit info
                const visitInfoContent = `
                    <div>
                        <strong>${{locationName}}</strong><br>
                        <p>${{visitDate}}</p>
                    </div>
                `
                document.getElementById('newVisitInfo').innerHTML = visitInfoContent;

                const comparisons = visitResult['comparisons']

                // If there are no comparisons to be made, immediately refresh the page
                if (comparisons.length == 0) {{
                    window.location.reload();
                }}

                var newComparisonFormContent = "<h2>Which is Better?</h2>";
                for (var i=0; i < comparisons.length; i++) {{
                    const comparison = comparisons[i]
                    const comparisonForm = await createNewComparisonForm(comparison, locationName)

                    newComparisonFormContent = `
                        ${{newComparisonFormContent}}
                        ${{comparisonForm}}
                    `
                }}
                document.getElementById('newComparisonInfo').innerHTML = newComparisonFormContent;
            }});

            async function submitComparisonForm(comparison_id) {{
                // TODO: disable form on submit
                // TODO: when final form is submitted, refresh page
                // e.preventDefault();
                const selected = document.querySelector(`input[name="better_${{comparison_id}}"]:checked`);
                if (selected === null || selected === undefined) {{
                    return;
                }} else {{
                    console.log('You selected: ' + selected.value);
                }}

                // PUT comparison
                const visitResponse = await fetch('/api/comparison', {{
                    method: 'PUT',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        id: comparison_id,
                        better: selected.value
                    }})
                }});

                document.getElementById(`comparisonForm_${{comparison_id}}`).setAttribute('inert', '')
                completedComparisonIds.add(comparison_id)

                // If all comparisons have been completed, refresh the page
                if (expectedComparisonIds.difference(completedComparisonIds).size == 0) {{
                    window.location.reload()
                }}
            }}
        </script>
    </body>
    </html>
    """