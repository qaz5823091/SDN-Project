const host_name = document.getElementById('host-name').innerText
const URL_PREFIX = 'http://api.sdn.com/learning/host/'
const information = document.getElementById('information')
const learning_list = document.getElementById('learning-sites')
const entertainment_list = document.getElementById('entertainment-sites')
const learning_range = document.getElementById('learning-range')
const entertainment_range = document.getElementById('entertainment-range')
const learning_range_value = document.getElementById('learning-range-value')
const entertainment_range_value = document.getElementById('entertainment-range-value')

const learning_sites_ip = document.getElementById('learning-sites-ip')
const learning_sites_button = document.getElementById('learning-sites-button')
const entertainment_sites_ip = document.getElementById('entertainment-sites-ip')
const entertainment_sites_button = document.getElementById('entertainment-sites-button')

var learning_remove_buttons, entertainment_remove_buttons

var learning_sites, learning_ratio, entertainment_sites, entertainment_ratio

const ip_pattern = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
const domain_pattern = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$/	

var current_seconds = 0, timer
const IDEL_TIME = 3

async function learningSitesButtonListener(event) {
	var value = learning_sites_ip.value
	if (value == "") {
		alert("IP must not be empty!")
	}
	else if (! (ip_pattern.test(value) || domain_pattern.test(value)) ) {
		alert("It is not an IP!")
	}
	else {
		const response = await fetch(
			URL_PREFIX + host_name + '/learning-sites/add', {
				method: 'POST',
				body: JSON.stringify({
					ip: value
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
	}

	location.reload()
}

async function entertainmentSitesButtonListener(event) {
	var value = entertainment_sites_ip.value
	if (value == "") {
		alert("IP must not be empty!")
	}
	else if (! (ip_pattern.test(value) || domain_pattern.test(value)) ) {
		alert("It is not an IP!")
	}
	else {
		const response = await fetch(
			URL_PREFIX + host_name + '/entertainment-sites/add', {
				method: 'POST',
				body: JSON.stringify({
					ip: value
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
	}

	location.reload()
}

async function learningRemoveButtonListener(event) {
	const response = await fetch(
		URL_PREFIX + host_name + '/learning-sites/remove', {
			method: 'POST',
			body: JSON.stringify({
				ip: event.target.value
			})
		})
		.then(response => response.status)
		.then((status) => {
			if (status == 200) {
				alert("Remove successfully!")
			}
			else {
				alert("Remove failed!")
			}
		})

	location.reload()
}

async function entertainmentRemoveButtonListener(event) {
	const response = await fetch(
		URL_PREFIX + host_name + '/entertainment-sites/remove', {
			method: 'POST',
			body: JSON.stringify({
				ip: event.target.value
			})
		})
		.then(response => response.status)
		.then((status) => {
			if (status == 200) {
				alert("Remove successfully!")
			}
			else {
				alert("Remove failed!")
			}
		})

	location.reload()
}

function initialComponents() {
	learning_range.addEventListener("input", (event) => {
		learning_range_value.innerHTML = event.target.value
		//console.log(event.target.value)
		fetch(URL_PREFIX + host_name + '/ratio/learning/' + event.target.value)
	})

	entertainment_range.addEventListener("input", (event) => {
		entertainment_range_value.innerHTML = event.target.value
		//console.log(event.target.value)
		fetch(URL_PREFIX + host_name + '/ratio/entertainment/' + event.target.value)
	})

	learning_sites_button.addEventListener("click", learningSitesButtonListener)
	entertainment_sites_button.addEventListener("click", entertainmentSitesButtonListener)

	learning_remove_buttons = document.querySelectorAll('button[site="learning"]')
	entertainment_remove_buttons = document.querySelectorAll('button[site="entertainment"]')

	learning_remove_buttons.forEach((button) => {
		button.addEventListener("click", learningRemoveButtonListener)
	})

	entertainment_remove_buttons.forEach((button) => {
		button.addEventListener("click", entertainmentRemoveButtonListener)
	})
}

function startTimer() {
	current_seconds++

	if (current_seconds > IDEL_TIME) {
		resetTimer()
		location.reload()
	}
}

function resetTimer() {
	clearInterval(timer)
    current_seconds = 0
    timer = setInterval(startTimer, 1000)
}

function setIdleReload() {
	window.onload = resetTimer
	window.onmousemove = resetTimer
	window.onmousedown = resetTimer
	window.ontouchstart = resetTimer
	window.onclick = resetTimer
	window.onkeypress = resetTimer
}

function main() {
	initialComponents()
	setIdleReload()
}

main()
