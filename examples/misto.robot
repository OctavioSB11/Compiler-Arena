// Misto: persegue o inimigo, atira quando está perto e patrulha quando não o vê
robot Misto {
  int contador = 0;
  bool perto;

  while energy > 10 {
    scan();
    perto = enemy.distance < 200;
    if enemy.visible && !perto {
      move(10);
    } else if enemy.visible && perto {
      fire(2);
    } else {
      contador = contador + 1;
      if contador > 5 {
        rotate(-45);
        contador = 0;
      }
      move(3);
    }
  }
}