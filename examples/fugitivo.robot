// Fugitivo: mantém distância do inimigo e recua quando a energia está baixa
robot Fugitivo {
  bool emPerigo;

  while true {
    scan();
    emPerigo = energy < 30 || enemy.distance < 100;
    if emPerigo && enemy.visible {
      back(15);
      rotate(90);
    } else {
      move(5);
    }
  }
}