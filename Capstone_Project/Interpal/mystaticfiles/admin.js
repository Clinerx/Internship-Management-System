const sidebar = document.getElementById("sidebar");
const toggleSidebarButton = document.getElementById("toggleSidebar");
const mainContent = document.getElementById("mainContent");

const dashboardLink = document.getElementById("dashboardLink");
const departmentsLink = document.getElementById("departmentsLink");
const advisorsLink = document.getElementById("advisorsLink");
const internshipDatesLink = document.getElementById("internshipDatesLink");
const accountApprovalLink = document.getElementById("accountApprovalLink");
const internTransactionsLink = document.getElementById(
  "internTransactionsLink"
);
const internshipProceduresLink = document.getElementById(
  "internshipProceduresLink"
);

const dashboardContent = document.getElementById("dashboardContent");
const departmentsContent = document.getElementById("departmentsContent");
const advisorsContent = document.getElementById("advisorsContent");
const internshipDatesContent = document.getElementById(
  "internshipDatesContent"
);
const accountApprovalContent = document.getElementById(
  "accountApprovalContent"
);
const internTransactionsContent = document.getElementById(
  "internTransactionsContent"
);
const internshipProceduresContent = document.getElementById(
  "internshipProceduresContent"
);


// Show content based on the sidebar link clicked
function showContent(contentId) {
  dashboardContent.style.display = "none";
  departmentsContent.style.display = "none";
  advisorsContent.style.display = "none";
  internshipDatesContent.style.display = "none";
  accountApprovalContent.style.display = "none";
  internTransactionsContent.style.display = "none";
  internshipProceduresContent.style.display = "none";

  document.getElementById(contentId).style.display = "block";
}

dashboardLink.addEventListener("click", () => showContent("dashboardContent"));
departmentsLink.addEventListener("click", () =>
  showContent("departmentsContent")
);
advisorsLink.addEventListener("click", () => showContent("advisorsContent"));
internshipDatesLink.addEventListener("click", () =>
  showContent("internshipDatesContent")
);
accountApprovalLink.addEventListener("click", () =>
  showContent("accountApprovalContent")
);
internTransactionsLink.addEventListener("click", () =>
  showContent("internTransactionsContent")
);
internshipProceduresLink.addEventListener("click", () =>
  showContent("internshipProceduresContent")
);

//para sa modal ng advisor maadd sa table ang inputed na data
document
  .getElementById("addAdvisorForm")
  .addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent form submission

    // Get form values
    const advisorName = document.getElementById("advisorName").value;
    const department = document.getElementById("department").value;
    const contact = document.getElementById("contact").value;

    // Get the advisors table body
    const tableBody = document.querySelector("#advisorsContent table tbody");

    // Create a new row
    const newRow = document.createElement("tr");
    const rowCount = tableBody.rows.length + 1;

    newRow.innerHTML = `
    <td>${rowCount}</td>
    <td>${advisorName}</td>
    <td>${department}</td>
    <td>${contact}</td>
    <td>
      <button class="btn btn-warning btn-sm">Edit</button>
      <button class="btn btn-danger btn-sm delete-advisor-btn">Delete</button>
    </td>
  `;

    // Append the new row to the table
    tableBody.appendChild(newRow);

    // Clear the form fields
    document.getElementById("addAdvisorForm").reset();

    // Close the modal
    const modal = bootstrap.Modal.getInstance(
      document.getElementById("addAdvisorModal")
    );
    modal.hide();
  });

//delete btn in aadvisor
document.addEventListener("click", function (event) {
  if (event.target.classList.contains("delete-advisor-btn")) {
    const row = event.target.closest("tr"); // Get the closest row containing the button
    const advisorName = row.querySelector("td:nth-child(2)").textContent; // Advisor Name from the row

    const confirmDelete = confirm(
      `Are you sure you want to delete advisor "${advisorName}"?`
    );
    if (confirmDelete) {
      row.remove(); // Remove the row from the table
      alert(`Advisor "${advisorName}" has been deleted.`);
    }
  }
});

// para to sa uploadfile sa dashboard
document
  .getElementById("image-upload")
  .addEventListener("change", function (event) {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = function (e) {
      const imgPreview = document.createElement("img");
      imgPreview.src = e.target.result;
      imgPreview.style.width = "100px"; // Set desired width
      document.body.appendChild(imgPreview); // Append to a specific section
    };
    reader.readAsDataURL(file);
  });
// para ito sa table ng student sa dashboard
$(document).ready(function () {
  $("table").DataTable();
});
// delete sa student table sa dashboard
document.addEventListener("click", function (event) {
  if (event.target.classList.contains("delete-student-btn")) {
    const row = event.target.closest("tr");
    const studentName = row.querySelector("td:nth-child(2)").textContent;

    if (confirm(`Are you sure you want to delete ${studentName}?`)) {
      row.remove();
      alert(`${studentName} has been deleted.`);
    }
  }
});

// PARA SA approval add or decline
// Filter functionality for Approved and Declined buttons
// Approve or decline logic
document.addEventListener("click", function (event) {
    if (event.target.classList.contains("approve-btn")) {
      const row = event.target.closest("tr");
      const studentName = row.querySelector("td:nth-child(2)").textContent;
  
      if (confirm(`Are you sure you want to approve ${studentName}'s account?`)) {
        // Update the status
        row.dataset.status = "approved"; // Update the data status
        row.querySelector("td:nth-child(5)").textContent = "Approved"; // Update the status text
        alert(`${studentName}'s account has been approved.`);
      }
    }
  
    if (event.target.classList.contains("decline-btn")) {
      const row = event.target.closest("tr");
      const studentName = row.querySelector("td:nth-child(2)").textContent;
  
      if (confirm(`Are you sure you want to decline ${studentName}'s account?`)) {
        // Update the status
        row.dataset.status = "declined"; // Update the data status
        row.querySelector("td:nth-child(5)").textContent = "Declined"; // Update the status text
        alert(`${studentName}'s account has been declined.`);
      }
    }
  });
  
  // Show Approved Button
  document.getElementById("showApproved").addEventListener("click", function () {
    const rows = document.querySelectorAll("#approvalTable tbody tr");
    rows.forEach(row => {
      row.style.display = row.dataset.status === "approved" ? "" : "none"; // Show approved rows
    });
  });
  
  // Show Declined Button
  document.getElementById("showDeclined").addEventListener("click", function () {
    const rows = document.querySelectorAll("#approvalTable tbody tr");
    rows.forEach(row => {
      row.style.display = row.dataset.status === "declined" ? "" : "none"; // Show declined rows
    });
  });
  
  // Show All Button
  document.getElementById("showAll").addEventListener("click", function () {
    const rows = document.querySelectorAll("#approvalTable tbody tr");
    rows.forEach(row => {
      row.style.display = ""; // Show all rows
    });
  });

  // internship transactionbmdfivheiufvs

  // Handle Add Transaction Form Submission
document.getElementById("addTransactionForm").addEventListener("submit", function (event) {
  event.preventDefault(); // Prevent form from reloading the page

  // Retrieve form data
  const internName = document.getElementById("internName").value;
  const organizationName = document.getElementById("organizationName").value;
  const transactionDate = document.getElementById("transactionDate").value;
  const description = document.getElementById("description").value;

  // Get the transactions table body
  const tableBody = document.getElementById("transactionsTableBody");

  // Create a new row
  const rowCount = tableBody.rows.length + 1; // Determine the row number
  const newRow = document.createElement("tr");

  // Populate the row with form data
  newRow.innerHTML = `
    <td>${rowCount}</td>
    <td>${internName}</td>
    <td>${organizationName}</td>
    <td>${transactionDate}</td>
    <td>${description}</td>
    <td>
      <button class="btn btn-warning btn-sm">Edit</button>
      <button class="btn btn-danger btn-sm delete-transaction-btn">Delete</button>
    </td>
  `;

  // Append the new row to the table
  tableBody.appendChild(newRow);

  // Clear the form
  document.getElementById("addTransactionForm").reset();

  // Close the modal
  const modal = bootstrap.Modal.getInstance(document.getElementById("addTransactionModal"));
  modal.hide();

  // Optional: Show a confirmation message
  alert(`Transaction added successfully for ${internName}`);
});

// Sample data for internship opportunities
const internshipOpportunities = [
  { id: 1, title: "Software Development Internship", organization: "Tech Company A", postedDate: "2024-01-01", status: "Pending" },
  { id: 2, title: "Data Science Internship", organization: "Tech Company B", postedDate: "2024-01-05", status: "Pending" },
  // Add more internships as needed
];

// Array to hold confirmed internships
const confirmedInternships = [];

// Load internship opportunities into the view table
function loadInternshipOpportunities() {
  const opportunitiesTbody = document.getElementById("internship-opportunities-body");
  opportunitiesTbody.innerHTML = ""; // Clear existing rows

  internshipOpportunities.forEach((internship) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${internship.id}</td>
      <td>${internship.title}</td>
      <td>${internship.organization}</td>
      <td>${internship.postedDate}</td>
      <td>${internship.status}</td>
      <td>
        <button class="btn btn-info btn-sm" onclick="viewInternship(${internship.id})">View</button>
        <button class="btn btn-success btn-sm" onclick="confirmInternship(${internship.id})">Confirm</button>
      </td>
    `;
    opportunitiesTbody.appendChild(row);
  });
}

// Load confirmed internships into the confirm table
function loadConfirmedInternships() {
  const confirmedTbody = document.getElementById("confirm-internship-body");
  confirmedTbody.innerHTML = ""; // Clear existing rows

  confirmedInternships.forEach((internship) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${internship.id}</td>
      <td>${internship.title}</td>
      <td>${internship.organization}</td>
      <td>${internship.postedDate}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="removeConfirmation(${internship.id})">Remove</button>
      </td>
    `;
    confirmedTbody.appendChild(row);
  });
}

// View internship details
function viewInternship(id) {
  const internship = internshipOpportunities.find(i => i.id === id);
  if (internship) {
    alert(`Internship Title: ${internship.title}\nOrganization: ${internship.organization}\nPosted Date: ${internship.postedDate}`);
  }
}

// Confirm internship and move it to confirmed internships
function confirmInternship(id) {
  const internshipIndex = internshipOpportunities.findIndex(i => i.id === id);
  if (internshipIndex !== -1) {
    const confirmedInternship = internshipOpportunities[internshipIndex];
    confirmedInternship.status = "Confirmed"; // Update status
    confirmedInternships.push(confirmedInternship); // Add to confirmed internships
    internshipOpportunities.splice(internshipIndex, 1); // Remove from opportunities
    loadInternshipOpportunities(); // Reload the view table
    loadConfirmedInternships(); // Reload the confirmed table
    alert(`Internship "${confirmedInternship.title}" has been confirmed.`);
  }
}

// Remove confirmation from the confirmed internships table
function removeConfirmation(id) {
  const confirmedIndex = confirmedInternships.findIndex(i => i.id === id);
  if (confirmedIndex !== -1) {
    const removedInternship = confirmedInternships.splice(confirmedIndex, 1)[0]; // Remove from confirmed internships
    internshipOpportunities.push(removedInternship); // Add back to opportunities
    loadInternshipOpportunities(); // Reload the view table
    loadConfirmedInternships(); // Reload the confirmed table
    alert(`Internship "${removedInternship.title}" has been removed from confirmed.`);
  }
}
//baba na to ayy para sa django na mahandle ang modal form

$(document).ready(function() {
    $('#addAdvisorForm').on('submit', function(e) {
        e.preventDefault();
        // AJAX call to submit the form data
        $.ajax({
            type: 'POST',
            url: '{% url "add_advisor" %}',  // URL to your Django view
            data: $(this).serialize(),
            success: function(response) {
                // Handle success (e.g., update the table)
                $('#addAdvisorModal').modal('hide');
                location.reload();  // Reload the page to see the updates
            },
            error: function(error) {
                // Handle error
                alert('Error adding advisor.');
            }
        });
    });
});

// Call this function to load internships when the page is ready
loadInternshipOpportunities();



// Show the default dashboard content when the page loads
showContent("dashboardContent");
