document
    .getElementById("loginForm")
    .addEventListener("submit", function(event) {

        event.preventDefault();


        let email =
            document.getElementById("email").value;


        let password =
            document.getElementById("password").value;


        if (email === "" || password === "") {

            document.getElementById(
                "loginMessage"
            ).innerHTML =
                "Please enter email and password.";

            return;
        }


        /*
        Later Person 2 can connect:

        POST /api/login

        Example:

        fetch("/api/login", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        */


        alert("Login API is not connected yet.");

    });