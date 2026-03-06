async function sendMessage(){

let input = document.getElementById("message")

let message = input.value

if(message == "") return

addMessage(message,"user")

input.value = ""

let response = await fetch("/chatbot_message",{

method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({message:message})

})

let data = await response.json()

typingEffect(data.response)

}

function addMessage(text,type){

let chat = document.getElementById("chatbox")

let div = document.createElement("div")

div.className = type == "user" ? "user" : "bot"

div.innerText = text

chat.appendChild(div)

chat.scrollTop = chat.scrollHeight

}

function typingEffect(text){

let chat = document.getElementById("chatbox")

let div = document.createElement("div")

div.className = "bot"

chat.appendChild(div)

let i = 0

let interval = setInterval(()=>{

div.innerText = text.substring(0,i)

i++

if(i > text.length){
clearInterval(interval)
}

chat.scrollTop = chat.scrollHeight

},30)

}