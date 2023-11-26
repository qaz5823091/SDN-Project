const URL_PREFIX = 'http://localhost:8080/learning/add-host'
const add_button = document.getElementById("learning-add-host-button")
const select = document.getElementById("learning-add-host-select")

add_button.addEventListener('click', (event) => {
	const response = fetch(
		URL_PREFIX, {
			method: 'POST',
			body: JSON.stringify({
				ip: select.value
			})
		})
		.then(response => response.status)
		.then((status) => {
			if (status == 200) {
				alert("Add successfully!")
			}
			else {
				alert("Add failed!")
			}
		})
})