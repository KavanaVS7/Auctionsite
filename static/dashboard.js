document.addEventListener('DOMContentLoaded', () => {
    fetch('dashboard.php')
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
        } else {
          document.getElementById('user-name').textContent = data.name;
          document.getElementById('user-email').textContent = data.email;
          document.getElementById('user-registration-date').textContent = data.registration_date;
        }
      })
      .catch(error => console.error('Error fetching user data:', error));
  });
  