fetch("/api/equipment")

    .then(function(response) {

        return response.json();

    })

    .then(function(data) {


        let total =
            data.length;


        let available =
            data.filter(function(item) {

                return item.available_quantity > 0;

            }).length;


        document.getElementById(
            "totalEquipment"
        ).innerHTML = total;


        document.getElementById(
            "availableEquipment"
        ).innerHTML = available;

    })

    .catch(function(error) {

        console.log(error);

        document.getElementById(
            "totalEquipment"
        ).innerHTML = "0";


        document.getElementById(
            "availableEquipment"
        ).innerHTML = "0";

    });