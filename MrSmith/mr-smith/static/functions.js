document.addEventListener('DOMContentLoaded', function() {
    function sum_amt() {
        var trNodes = document.querySelectorAll('.table tbody tr');
        trNodes.forEach(function(trNode) {
            var qtyElement = trNode.querySelector('.qty');
            var priceElement = trNode.querySelector('.price');
            var totalElement = trNode.querySelector('.total');

            if (!qtyElement || !priceElement || !totalElement) {
                console.log('Missing element:', {
                    qtyElement: qtyElement,
                    priceElement: priceElement,
                    totalElement: totalElement,
                    trNode: trNode
                });
                return;
            }

            var qty = qtyElement.value;
            var price = priceElement.innerText.replace('g', '');
            var answer = (Number(qty) * Number(price));
            totalElement.value = answer;
        });
    }

    var qtyInputs = document.querySelectorAll('.qty');
    qtyInputs.forEach(function(input) {
        input.addEventListener('input', sum_amt);
    });

    window.showMerchants = function() {
        document.getElementById("ingredients").style.display = "block";
        document.getElementById("wares").style.display = "none";
    }
    window.showWares = function() {
        document.getElementById("ingredients").style.display = "none";
        document.getElementById("wares").style.display = "block";
    }

    window.showFood = function() {
        document.getElementById("food").style.display = "block";
        document.getElementById("drink").style.display = "none";
        document.getElementById("lodging").style.display = "none";
    }
    window.showDrink = function() {
        document.getElementById("food").style.display = "none";
        document.getElementById("drink").style.display = "block";
        document.getElementById("lodging").style.display = "none";
    }
    window.showLodging = function() {
        document.getElementById("food").style.display = "none";
        document.getElementById("drink").style.display = "none";
        document.getElementById("lodging").style.display = "block";
    }
});

