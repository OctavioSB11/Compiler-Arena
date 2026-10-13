// Atirador: gira procurando o inimigo e atira com mais força de perto
robot Atirador {
  int distancia;

  while energy > 0 {
    scan();
    if enemy.visible {
      distancia = enemy.distance;
      if distancia < 150 {
        fire(3);
      } else if distancia < 400 {
        fire(2);
      } else {
        fire(1);
      }
    } else {
      rotate(30);
    }
  }
}