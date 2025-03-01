db = db.getSiblingDB("admin");

db.createUser({
  user: "chill_user",
  pwd: "chill_user_pwd",
  roles: [
    { role: "readWrite", db: "schedule" }
  ]
});
