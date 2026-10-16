-- =====================================================================
-- Cali Burger - dados de exemplo
-- Todas as contas de exemplo usam a senha 123456.
--   Cliente:     usuário joao  (ou maria)
--   Balconista:  CPF 352.658.110-01
--   Cozinheiro:  CPF 211.996.250-27
-- Os CPFs são fictícios (gerados apenas para passar na validação).
-- =====================================================================

USE db_caliburger;
SET NAMES utf8mb4;

INSERT INTO categoria (id, nome) VALUES (1, 'Lanches'), (2, 'Acompanhamentos'), (3, 'Bebidas');

INSERT INTO cardapio (id, nome, descricao, preco, imagem, categoria_id) VALUES
    (1, 'Cali Clássico', 'Hambúrguer 180 g com queijo cheddar, alface e tomate no pão brioche', 22.00, 'cali_classico.webp', 1),
    (2, 'Cali Duplo', 'Dois hambúrgueres 180 g, cheddar duplo e pão brioche', 28.00, 'cali_duplo.webp', 1),
    (3, 'X-Burger', 'Hambúrguer 180 g com queijo cheddar e molho especial', 20.00, 'x_burger.webp', 1),
    (4, 'Cali Fritas', 'Porção de batata frita (180 g)', 15.00, 'cali_fritas.webp', 2),
    (5, 'Cali Nuggets', '10 nuggets de frango', 12.00, 'cali_nugget.webp', 2),
    (6, 'Suco de Uva', 'Copo de suco de uva (400 ml)', 8.00, 'suco_uva.webp', 3),
    (7, 'Refrigerante', 'Copo de refrigerante (400 ml)', 8.00, 'refrigerante.webp', 3),
    (8, 'Água', 'Garrafa de água mineral (500 ml)', 5.00, 'agua.webp', 3);

-- Quantidades já descontando o consumo dos pedidos de exemplo abaixo.
INSERT INTO estoque (id_ingrediente, nome_ingrediente, quantidade) VALUES
    (1, 'Pão Brioche', 110),
    (2, 'Hambúrguer 180 g', 76),
    (3, 'Queijo Cheddar', 86),
    (4, 'Alface', 9),
    (5, 'Tomate', 37),
    (6, 'Suco de uva', 0),
    (7, 'Refrigerante', 73),
    (8, 'Água', 58),
    (9, 'Batata frita', 65),
    (10, 'Nugget de frango', 20);

INSERT INTO cardapio_ingrediente (id_cardapio, id_ingrediente, quantidade_utilizada) VALUES
    (1, 1, 1),
    (1, 2, 1),
    (1, 3, 1),
    (1, 4, 1),
    (1, 5, 1),
    (2, 1, 1),
    (2, 2, 2),
    (2, 3, 2),
    (3, 1, 1),
    (3, 2, 1),
    (3, 3, 1),
    (4, 9, 1),
    (5, 10, 10),
    (6, 6, 1),
    (7, 7, 1),
    (8, 8, 1);

INSERT INTO cliente (id, login, senha, nome, email, cpf, data_nasc, end_estado, end_cidade, end_bairro, end_logradouro) VALUES
    (1, 'joao', '$2y$10$EL8QETi4P7KQ6QRlhIJSR.3Jo4EpkhpCQA6X6EYy0OD61sHo9KGSy', 'João Silva', 'joao@exemplo.com', '28962080036', '1990-01-01', 'PR', 'Curitiba', 'Centro', 'Rua XV de Novembro, 100'),
    (2, 'maria', '$2y$10$EL8QETi4P7KQ6QRlhIJSR.3Jo4EpkhpCQA6X6EYy0OD61sHo9KGSy', 'Maria Souza', 'maria@exemplo.com', '10106081004', '1995-02-02', 'PR', 'Curitiba', 'Batel', 'Avenida do Batel, 321');

INSERT INTO balconista_dono (cpf, nome, data_nasc, email, sexo, senha) VALUES
    ('35265811001', 'Ana Ribeiro', '1985-01-01', 'admin@caliburger.com', 'Feminino', '$2y$10$EL8QETi4P7KQ6QRlhIJSR.3Jo4EpkhpCQA6X6EYy0OD61sHo9KGSy');

INSERT INTO cozinheiro (cpf, nome, data_nasc, sexo, email, senha) VALUES
    ('21199625027', 'Carlos Souza', '1990-05-10', 'Masculino', 'carlos@caliburger.com', '$2y$10$EL8QETi4P7KQ6QRlhIJSR.3Jo4EpkhpCQA6X6EYy0OD61sHo9KGSy'),
    ('41368460020', 'Juliana Alves', '1988-03-30', 'Feminino', 'juliana@caliburger.com', '$2y$10$EL8QETi4P7KQ6QRlhIJSR.3Jo4EpkhpCQA6X6EYy0OD61sHo9KGSy');

INSERT INTO pedido (numero_do_pedido, id_cliente, nome_cliente, valor, status, data_pedido) VALUES
    (1, 1, 'João Silva', 75.00, 'Concluído', DATE_SUB(NOW(), INTERVAL 9240 MINUTE)),
    (2, 2, 'Maria Souza', 36.00, 'Concluído', DATE_SUB(NOW(), INTERVAL 7620 MINUTE)),
    (3, 1, 'João Silva', 20.00, 'Cancelado/recusado', DATE_SUB(NOW(), INTERVAL 6060 MINUTE)),
    (4, 2, 'Maria Souza', 37.00, 'Concluído', DATE_SUB(NOW(), INTERVAL 4520 MINUTE)),
    (5, 1, 'João Silva', 102.00, 'Concluído', DATE_SUB(NOW(), INTERVAL 1530 MINUTE)),
    (6, 1, 'João Silva', 43.00, 'A caminho', DATE_SUB(NOW(), INTERVAL 40 MINUTE)),
    (7, 2, 'Maria Souza', 56.00, 'Em preparação', DATE_SUB(NOW(), INTERVAL 20 MINUTE)),
    (8, 1, 'João Silva', 27.00, 'Aguardando aceitação', DATE_SUB(NOW(), INTERVAL 6 MINUTE)),
    (9, 2, 'Maria Souza', 23.00, 'Aguardando aceitação', DATE_SUB(NOW(), INTERVAL 2 MINUTE));

INSERT INTO itens_pedido (numero_do_pedido, id_cardapio, produto, quantidade, valor, observacao) VALUES
    (1, 1, 'Cali Clássico', 2, 44.00, NULL),
    (1, 4, 'Cali Fritas', 1, 15.00, NULL),
    (1, 7, 'Refrigerante', 2, 16.00, NULL),
    (2, 2, 'Cali Duplo', 1, 28.00, NULL),
    (2, 6, 'Suco de Uva', 1, 8.00, NULL),
    (3, 3, 'X-Burger', 1, 20.00, NULL),
    (4, 3, 'X-Burger', 1, 20.00, NULL),
    (4, 5, 'Cali Nuggets', 1, 12.00, NULL),
    (4, 8, 'Água', 1, 5.00, NULL),
    (5, 2, 'Cali Duplo', 2, 56.00, NULL),
    (5, 4, 'Cali Fritas', 2, 30.00, NULL),
    (5, 7, 'Refrigerante', 2, 16.00, NULL),
    (6, 2, 'Cali Duplo', 1, 28.00, NULL),
    (6, 4, 'Cali Fritas', 1, 15.00, NULL),
    (7, 3, 'X-Burger', 2, 40.00, 'Sem molho especial'),
    (7, 7, 'Refrigerante', 2, 16.00, NULL),
    (8, 1, 'Cali Clássico', 1, 22.00, 'Carne bem passada'),
    (8, 8, 'Água', 1, 5.00, NULL),
    (9, 4, 'Cali Fritas', 1, 15.00, NULL),
    (9, 7, 'Refrigerante', 1, 8.00, NULL);

INSERT INTO pedido_estoque (numero_do_pedido, id_ingrediente, quantidade) VALUES
    (1, 1, 2),
    (1, 2, 2),
    (1, 3, 2),
    (1, 4, 2),
    (1, 5, 2),
    (1, 7, 2),
    (1, 9, 1),
    (2, 1, 1),
    (2, 2, 2),
    (2, 3, 2),
    (2, 6, 1),
    (4, 1, 1),
    (4, 2, 1),
    (4, 3, 1),
    (4, 8, 1),
    (4, 10, 10),
    (5, 1, 2),
    (5, 2, 4),
    (5, 3, 4),
    (5, 7, 2),
    (5, 9, 2),
    (6, 1, 1),
    (6, 2, 2),
    (6, 3, 2),
    (6, 9, 1),
    (7, 1, 2),
    (7, 2, 2),
    (7, 3, 2),
    (7, 7, 2),
    (8, 1, 1),
    (8, 2, 1),
    (8, 3, 1),
    (8, 4, 1),
    (8, 5, 1),
    (8, 8, 1),
    (9, 7, 1),
    (9, 9, 1);

INSERT INTO pagamento (data_hora, forma_de_pagamento, valor, numero_do_pedido, id_cliente) VALUES
    (DATE_SUB(NOW(), INTERVAL 9240 MINUTE), 'PIX', 75.00, 1, 1),
    (DATE_SUB(NOW(), INTERVAL 7620 MINUTE), 'PIX', 36.00, 2, 2),
    (DATE_SUB(NOW(), INTERVAL 6060 MINUTE), 'PIX', 20.00, 3, 1),
    (DATE_SUB(NOW(), INTERVAL 4520 MINUTE), 'PIX', 37.00, 4, 2),
    (DATE_SUB(NOW(), INTERVAL 1530 MINUTE), 'PIX', 102.00, 5, 1),
    (DATE_SUB(NOW(), INTERVAL 40 MINUTE), 'PIX', 43.00, 6, 1),
    (DATE_SUB(NOW(), INTERVAL 20 MINUTE), 'PIX', 56.00, 7, 2),
    (DATE_SUB(NOW(), INTERVAL 6 MINUTE), 'PIX', 27.00, 8, 1),
    (DATE_SUB(NOW(), INTERVAL 2 MINUTE), 'PIX', 23.00, 9, 2);

