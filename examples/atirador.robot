// Atirador: gira procurando o inimigo, mira nele e atira com mais força de perto
robot Atirador {
  int mira = 0;
  int dif;
  int distancia;

  while energy > 0 {
    scan();
    if enemy.visible {
      dif = enemy.direction - mira;
      if dif > 180 {
        dif = dif - 360;
      }
      if dif < -180 {
        dif = dif + 360;
      }
      if dif > 8 || dif < -8 {
        rotate(dif);
        mira = mira + dif;
      } else {
        distancia = enemy.distance;
        if distancia < 150 {
          fire(3);
        } else if distancia < 400 {
          fire(2);
        } else {
          fire(1);
        }
      }
    } else {
      rotate(30);
      mira = mira + 30;
    }
    if mira >= 360 {
      mira = mira - 360;
    }
    if mira < 0 {
      mira = mira + 360;
    }
  }
}