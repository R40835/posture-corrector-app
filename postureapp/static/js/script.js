const inputs = document.querySelectorAll(".login-box input");

function addClass() {
	let parent = this.parentNode.parentNode;
	parent.classList.add("active");
}

function removeClass() {
	let parent = this.parentNode.parentNode;
	if (this.value == "") {
		parent.classList.remove("active");
	}
}

inputs.forEach(input => {
	input.addEventListener("focus", addClass);
	input.addEventListener("blur", removeClass);
});
