let equipmentList = [];


// Get equipment from Flask backend

fetch("/api/equipment")

    .then(function(response) {

        return response.json();

    })

    .then(function(data) {

        equipmentList = data;

        displayEquipment(equipmentList);

    })

    .catch(function(error) {

        console.log(error);

        document.getElementById("equipmentList").innerHTML =
            "<p>Unable to load equipment.</p>";

    });


// Display equipment

function displayEquipment(items) {

    let container =
        document.getElementById("equipmentList");

    container.innerHTML = "";


    if (items.length === 0) {

        container.innerHTML =
            "<p>No equipment found.</p>";

        return;
    }


    items.forEach(function(item) {

        let card =
            document.createElement("div");

        card.className = "equipment-card";


        card.innerHTML = `

            <h2>${item.name}</h2>

            <p>
                <strong>Category:</strong>
                ${item.category}
            </p>

            <p>
                <strong>Total:</strong>
                ${item.total_quantity}
            </p>

            <p>
                <strong>Available:</strong>
                ${item.available_quantity}
            </p>

            <p>
                <strong>Status:</strong>
                ${item.status}
            </p>

            <button onclick="viewEquipment(${item.id})">
                View Details
            </button>

        `;


        container.appendChild(card);

    });

}


// View equipment details

function viewEquipment(id) {

    window.location.href =
        "/student/equipment/" + id;

}


// Search

document
    .getElementById("searchBox")
    .addEventListener("keyup", function() {

        let search =
            this.value.toLowerCase();


        let filtered =
            equipmentList.filter(function(item) {

                return (
                    item.name
                        .toLowerCase()
                        .includes(search)

                    ||

                    item.category
                        .toLowerCase()
                        .includes(search)
                );

            });


        displayEquipment(filtered);

    });