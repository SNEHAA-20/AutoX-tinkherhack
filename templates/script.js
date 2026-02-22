let expenses = JSON.parse(localStorage.getItem("expenses")) || [];

function addExpense() {
    let title = document.getElementById("title").value;
    let amount = document.getElementById("amount").value;

    if (title === "" || amount === "") {
        alert("Please fill all fields");
        return;
    }

    let expense = {
        id: Date.now(),
        title: title,
        amount: Number(amount)
    };

    expenses.push(expense);
    localStorage.setItem("expenses", JSON.stringify(expenses));

    document.getElementById("title").value = "";
    document.getElementById("amount").value = "";

    displayExpenses();
}

function displayExpenses() {
    let list = document.getElementById("expenseList");
    let total = 0;

    list.innerHTML = "";

    expenses.forEach(exp => {
        total += exp.amount;

        let li = document.createElement("li");
        li.innerHTML = `${exp.title} - ₹${exp.amount}
        <button onclick="deleteExpense(${exp.id})">❌</button>`;

        list.appendChild(li);
    });

    document.getElementById("total").innerText = total;
}

function deleteExpense(id) {
    expenses = expenses.filter(exp => exp.id !== id);
    localStorage.setItem("expenses", JSON.stringify(expenses));
    displayExpenses();
}

displayExpenses();