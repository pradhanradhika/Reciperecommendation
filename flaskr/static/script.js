document.getElementById('ingredient-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const ingredientsInput = document.getElementById('ingredients').value.trim();

    document.getElementById('home').addEventListener('click', function() {
    window.location.href = '/';
});

document.getElementById('profile').addEventListener('click', function() {
    window.location.href = '/profile';
});



document.addEventListener("DOMContentLoaded", function () {
    const chatbotButton = document.getElementById("chatbot");
    const chatbotPopup = document.getElementById("chatbot-popup");
    const closeButton = document.querySelector(".close-btn");

    // Open the chatbot popup
    chatbotButton.addEventListener("click", function () {
        chatbotPopup.style.display = "block";
        window.open("http://127.0.0.1:7860", "_blank");
    });

    // Close the chatbot popup
    closeButton.addEventListener("click", function () {
        chatbotPopup.style.display = "none";
    });

    // Close the popup if the user clicks outside of it
    window.addEventListener("click", function (event) {
        if (event.target == chatbotPopup) {
            chatbotPopup.style.display = "none";
        }
    });
});


     if (!ingredientsInput) {
        alert("Please enter some ingredients!");
        return;
    }

    const ingredientsArray = ingredientsInput.split(',').map(ingredient => ingredient.trim());

    fetch('/find_recipe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ingredients: ingredientsArray }),
    })
    .then(response => response.json())
    .then(recipes => {
        const recipeContainer = document.getElementById('recipe-result');
        recipeContainer.innerHTML = '';  // Clear previous results

        if (recipes.length === 0) {
            recipeContainer.innerHTML = '<p>No matching recipes found.</p>';
            return;
        }

        recipes.forEach(recipe => {
            const recipeCard = document.createElement('div');
            recipeCard.classList.add('recipe-card');

            // Recipe Title
            const recipeTitle = document.createElement('h3');
            recipeTitle.textContent = recipe['name'] || "Untitled Recipe";
            recipeCard.appendChild(recipeTitle);

            // Recipe Ingredients
            const recipeIngredients = document.createElement('p');
            recipeIngredients.innerHTML = `<strong>Ingredients:</strong> ${recipe['ingredients'].join(', ')}`;
            recipeCard.appendChild(recipeIngredients);

            // Recipe Procedure
            const recipeProcedure = document.createElement('p');
            recipeProcedure.innerHTML = `<strong>Procedure:</strong> ${recipe['instructions'] || 'Procedure not available'}`;
            recipeCard.appendChild(recipeProcedure);

            recipeContainer.appendChild(recipeCard);
        });
    })
    .catch(error => {
        console.error('Error fetching recipes:', error);
        const recipeContainer = document.getElementById('recipe-result');
        recipeContainer.innerHTML = '<p>Something went wrong. Please try again later.</p>';
    });


});
