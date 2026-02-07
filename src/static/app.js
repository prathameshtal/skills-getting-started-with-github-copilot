document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Clear and populate activity select dropdown
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Display each activity
      for (const [name, details] of Object.entries(activities)) {
        // Create activity card
        const card = document.createElement("div");
        card.className = "activity-card";

        const availableSpots = details.max_participants - details.participants.length;

        card.innerHTML = `
          <h4>${name}</h4>
          <p><strong>Description:</strong> ${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Available Spots:</strong> ${availableSpots} / ${details.max_participants}</p>
          <div class="participants-section">
            <p class="participants-header"><strong>Current Participants:</strong></p>
            <ul class="participants-list">
              ${details.participants.length > 0
                ? details.participants.map(email => `<li>${email}</li>`).join('')
                : '<li class="no-participants">No participants yet</li>'}
            </ul>
          </div>
        `;

        activitiesList.appendChild(card);

        // Add to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      }
    } catch (error) {
      console.error("Error loading activities:", error);
      activitiesList.innerHTML = "<p class=\"error\">Failed to load activities. Please try again later.</p>";
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;
    const messageDiv = document.getElementById("message");

    if (!activity) {
      showMessage("Please select an activity", "error");
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (response.ok) {
        showMessage(data.message, "success");
        // Reload activities to show updated participant list
        fetchActivities();
        // Reset form
        signupForm.reset();
      } else {
        showMessage(data.detail || "An error occurred", "error");
      }
    } catch (error) {
      console.error("Error signing up:", error);
      showMessage("Failed to sign up. Please try again.", "error");
    }
  });

  function showMessage(text, type) {
    const messageDiv = document.getElementById("message");
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");

    // Hide message after 5 seconds
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Load activities when page loads
  fetchActivities();
});
