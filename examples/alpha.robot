robot Alpha {
  int distancia;
  distancia = enemy.distance;

  while enemy.visible {
    if distancia < 100 {
      fire(3);
    } else {
      move(20);
    }
    rotate(15);
  }
}
