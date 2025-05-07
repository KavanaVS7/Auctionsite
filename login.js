function showForm(formId) {
  const forms = document.querySelectorAll('.form');
  const tabs = document.querySelectorAll('.tab-button');

  forms.forEach(form => {
    form.classList.remove('active');
  });

  tabs.forEach(tab => {
    tab.classList.remove('active');
  });

  document.getElementById(`${formId}-form`).classList.add('active');
  document.querySelector(`.tab-button[onclick="showForm('${formId}')"]`).classList.add('active');
}
