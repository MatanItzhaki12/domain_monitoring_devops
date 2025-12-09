document.addEventListener('DOMContentLoaded', function() {
    console.log('Page is loaded!')
    // Define all constants at the beginning
    const Username = document.querySelector('#username');
    const Password = document.querySelector('#password');
    const PasswordConfirmation = document.querySelector('#password_confirmation');
    const ErrorMessage = document.querySelector('#error-message');
    const SuccessMessage = document.querySelector('#success-message');
    const Form = document.querySelector('form');
    const Title = document.querySelector('.title')
    
    Title.addEventListener('click', function() {
        window.location.href = '/';
    });

    // Form submission event listener
    Form.addEventListener('submit', function(event) {
        event.preventDefault();

        // reset messages
        SuccessMessage.style.display = 'none'
        ErrorMessage.style.display = 'none'

        // Display a message
        let name = Username.value;
        let pass = Password.value;
        let pass_conf = PasswordConfirmation.value;
        registerUser(name, pass, pass_conf);

        // Reset the form after submission
        event.target.reset();
    });

    // Function to get weather information
    async function registerUser(name, pass, pass_conf) {
        content = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: name,
                password: pass,
                password_confirmation: pass_conf
            })
        };
        const response = await fetch(`/register`, content);
        const data = await response.json();
        if ("error" in data){
            ErrorMessage.textContent = `${data["error"]}`
            ErrorMessage.style.display = 'block'
        }
        else {
            SuccessMessage.textContent = `${data["message"]}`
            SuccessMessage.style.display = 'block'
            setTimeout(function() { window.location.href = "/dashboard"; }, 2000); 
        }
    }
});
