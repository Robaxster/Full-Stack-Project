


// SERVICE EXPANSION

function toggleService(card) {

    const allCards =
        document.querySelectorAll(".service-card");

    allCards.forEach(function(item){

        if(item !== card){

            item.classList.remove("active");
        }

    });

    card.classList.toggle("active");
}



// REQUEST DEMO

function requestDemo() {

    alert(
        "Thank you for your interest in Smart Logistics. Our team will contact you shortly."
    );

}



// PAGE LOADED

document.addEventListener("DOMContentLoaded", function(){

    // LEARN MORE BUTTON

    const learnBtn =
        document.querySelector(".secondary-btn");

    if(learnBtn){

        learnBtn.addEventListener("click", function(){

            document
            .querySelector("#services")
            .scrollIntoView({
                behavior: "smooth"
            });

        });

    }

});
function toggleWhy(card){

    const allCards =
        document.querySelectorAll(".why-card");

    allCards.forEach(function(item){

        if(item !== card){

            item.classList.remove("active");
        }

    });

    card.classList.toggle("active");
}
