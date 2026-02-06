module.exports = {
  apps : [{
    name   : "nanobot",
    script : "./start_nanobot.bat",
    interpreter: "cmd",
    interpreter_args: "/c",
    autorestart: true,
    watch: false
  }]
}