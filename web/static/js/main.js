const URL_PREFIX = 'http://api.sdn.com/learning/'
var collapse = document.getElementsByClassName("collapsible")
var collapseList = document.getElementById("learning-collapse")
var collapseContainer = document.getElementById("learning-collapse-container")

async function getHosts() {
	const response = await fetch(URL_PREFIX + 'hosts')
		.then(status)
		.then(result => result.json())
		.catch(error => {
			console.log(error)
		})

	response.forEach((entity, index) => {
		var li = document.createElement("li")
		var a = document.createElement("a")
		var img = document.createElement("img")
		var span = document.createElement("span")
		a.setAttribute("href", "/learning/host/" + entity.name)
		a.setAttribute("class", "flex items-center p-2 text-gray-900 rounded-lg dark:text-white hover:bg-green-200 dark:hover:bg-gray-700 group")
		img.setAttribute("class", "w-6 h-6 ms-2 text-gray-500 transition duration-75 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white")
		img.src = "/static/images/icon_sidebar_computer.svg"
		span.setAttribute("class", "ml-3")
		span.innerHTML = "Host " + String(index + 1)
		a.appendChild(img)
		a.appendChild(span)
		li.appendChild(a)
		collapseList.appendChild(li)
	})
}

function generateHosts() {

}

Array.from(collapse).forEach((item) => {
	item.addEventListener("click", collapseListener)
})

function collapseListener() {
	var content = collapseContainer
	console.log(content)

	if (content.style.display === "block") {
		content.style.display = "none"
		this.src = "/static/images/icon_sidebar_down.svg"
	} else {
		content.style.display = "block"
		this.src = "/static/images/icon_sidebar_up.svg"
	}
}

await getHosts()
