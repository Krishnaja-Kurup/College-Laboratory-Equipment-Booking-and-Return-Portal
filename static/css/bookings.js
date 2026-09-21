fetch("/api/my-bookings")

    .then(function(response) {

        return response.json();

    })

    .then(function(data) {

        displayBookings(data);

    })

    .catch(function(error) {

        console.log(error);

        document.getElementById(
            "bookingTable"
        ).innerHTML = `

            <tr>

                <td colspan="6">
                    Booking API is not connected yet.
                </td>

            </tr>

        `;

    });


function displayBookings(bookings) {

    let table =
        document.getElementById(
            "bookingTable"
        );


    table.innerHTML = "";


    if (bookings.length === 0) {

        table.innerHTML = `

            <tr>

                <td colspan="6">
                    No bookings found.
                </td>

            </tr>

        `;

        return;
    }


    bookings.forEach(function(booking) {

        let row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                ${booking.equipment_name}
            </td>

            <td>
                ${booking.quantity}
            </td>

            <td>
                ${booking.booked_date}
            </td>

            <td>
                ${booking.due_date}
            </td>

            <td>
                ${booking.status}
            </td>

            <td>

                ${
                    booking.status === "Booked"

                    ?

                    `<button
                        onclick="returnEquipment(${booking.id})">
                        Return
                    </button>`

                    :

                    ""
                }

            </td>

        `;


        table.appendChild(row);

    });

}


function returnEquipment(id) {

    fetch(
        "/api/bookings/" + id + "/return",
        {
            method: "PUT"
        }
    )

    .then(function(response) {

        return response.json();

    })

    .then(function(data) {

        alert(data.message);

        location.reload();

    })

    .catch(function(error) {

        console.log(error);

        alert("Unable to return equipment.");

    });

}