let currentEquipmentId =
    window.location.pathname.split("/").pop();


fetch("/api/equipment")

    .then(function(response) {

        return response.json();

    })

    .then(function(data) {

        let equipment =
            data.find(function(item) {

                return item.id == currentEquipmentId;

            });


        if (!equipment) {

            document.getElementById(
                "equipmentDetails"
            ).innerHTML =
                "<p>Equipment not found.</p>";

            return;
        }


        displayDetails(equipment);

    })

    .catch(function(error) {

        console.log(error);

        document.getElementById(
            "equipmentDetails"
        ).innerHTML =
            "<p>Unable to load equipment.</p>";

    });


function displayDetails(item) {

    let container =
        document.getElementById(
            "equipmentDetails"
        );


    container.innerHTML = `

        <div class="equipment-detail">

            <h2>${item.name}</h2>

            <p>
                <strong>Category:</strong>
                ${item.category}
            </p>

            <p>
                <strong>Total Quantity:</strong>
                ${item.total_quantity}
            </p>

            <p>
                <strong>Available Quantity:</strong>
                ${item.available_quantity}
            </p>

            <p>
                <strong>Status:</strong>
                ${item.status}
            </p>


            ${
                item.available_quantity > 0

                ?

                `<button onclick="bookEquipment(${item.id})">
                    Book Equipment
                </button>`

                :

                `<button disabled>
                    Not Available
                </button>`
            }

        </div>

    `;
}


function bookEquipment(id) {

    /*
       Person 2 will provide the booking API.

       Example:

       POST /api/bookings
    */

    alert(
        "Booking API will be connected here."
    );

}