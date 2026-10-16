-- =====================================================================
-- Cali Burger - estrutura do banco de dados (MySQL 8 / MariaDB 10.5+)
--
-- No XAMPP: importe este arquivo e depois o 02_dados_exemplo.sql pelo
-- phpMyAdmin. No Docker, os dois são carregados automaticamente.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS db_caliburger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_caliburger;

SET NAMES utf8mb4;

-- ---------------------------------------------------------- Pessoas

CREATE TABLE cliente (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    login          VARCHAR(30)  NOT NULL UNIQUE,
    senha          VARCHAR(255) NOT NULL COMMENT 'hash bcrypt (password_hash)',
    nome           VARCHAR(100) NOT NULL,
    email          VARCHAR(255) NOT NULL,
    cpf            CHAR(11)     NOT NULL UNIQUE,
    data_nasc      DATE         NOT NULL,
    end_estado     VARCHAR(255) NOT NULL,
    end_cidade     VARCHAR(255) NOT NULL,
    end_bairro     VARCHAR(255) NOT NULL,
    end_logradouro VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE balconista_dono (
    cpf       CHAR(11)     PRIMARY KEY,
    nome      VARCHAR(100) NOT NULL,
    data_nasc DATE         NOT NULL,
    email     VARCHAR(255) NOT NULL,
    sexo      VARCHAR(20)  NOT NULL,
    senha     VARCHAR(255) NOT NULL COMMENT 'hash bcrypt (password_hash)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE cozinheiro (
    cpf       CHAR(11)     PRIMARY KEY,
    nome      VARCHAR(100) NOT NULL,
    data_nasc DATE         NOT NULL,
    email     VARCHAR(255) NOT NULL,
    sexo      VARCHAR(20)  NOT NULL,
    senha     VARCHAR(255) NOT NULL COMMENT 'hash bcrypt (password_hash)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------- Cardápio e estoque

CREATE TABLE categoria (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE cardapio (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    nome         VARCHAR(100)  NOT NULL,
    descricao    VARCHAR(255)  DEFAULT NULL,
    preco        DECIMAL(10,2) NOT NULL,
    imagem       VARCHAR(255)  DEFAULT NULL COMMENT 'arquivo em public/imagens/lanches',
    categoria_id INT           NOT NULL,
    CONSTRAINT chk_cardapio_preco CHECK (preco > 0),
    CONSTRAINT fk_cardapio_categoria FOREIGN KEY (categoria_id) REFERENCES categoria (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE estoque (
    id_ingrediente   INT AUTO_INCREMENT PRIMARY KEY,
    nome_ingrediente VARCHAR(50) NOT NULL UNIQUE,
    quantidade       INT         NOT NULL DEFAULT 0,
    -- O banco recusa estoque negativo, mesmo com dois pedidos ao mesmo tempo.
    CONSTRAINT chk_estoque_quantidade CHECK (quantidade >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Receita: quanto de cada ingrediente uma unidade do item consome.
CREATE TABLE cardapio_ingrediente (
    id_cardapio          INT NOT NULL,
    id_ingrediente       INT NOT NULL,
    quantidade_utilizada INT NOT NULL,
    PRIMARY KEY (id_cardapio, id_ingrediente),
    CONSTRAINT chk_receita_quantidade CHECK (quantidade_utilizada > 0),
    CONSTRAINT fk_receita_cardapio FOREIGN KEY (id_cardapio) REFERENCES cardapio (id) ON DELETE CASCADE,
    CONSTRAINT fk_receita_ingrediente FOREIGN KEY (id_ingrediente) REFERENCES estoque (id_ingrediente) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------- Pedidos

CREATE TABLE pedido (
    numero_do_pedido INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente       INT           DEFAULT NULL COMMENT 'NULL se a conta do cliente foi excluída',
    nome_cliente     VARCHAR(100)  NOT NULL,
    valor            DECIMAL(10,2) NOT NULL,
    status           VARCHAR(30)   NOT NULL DEFAULT 'Aguardando aceitação',
    data_pedido      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_pedido_status (status),
    KEY idx_pedido_data (data_pedido),
    CONSTRAINT fk_pedido_cliente FOREIGN KEY (id_cliente) REFERENCES cliente (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Nome e valor do produto ficam gravados: mudar o cardápio não altera pedidos antigos.
CREATE TABLE itens_pedido (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    numero_do_pedido INT           NOT NULL,
    id_cardapio      INT           DEFAULT NULL,
    produto          VARCHAR(100)  NOT NULL,
    quantidade       INT           NOT NULL,
    valor            DECIMAL(10,2) NOT NULL COMMENT 'subtotal (preço x quantidade)',
    observacao       VARCHAR(255)  DEFAULT NULL,
    CONSTRAINT chk_item_quantidade CHECK (quantidade > 0),
    CONSTRAINT fk_item_pedido FOREIGN KEY (numero_do_pedido) REFERENCES pedido (numero_do_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_item_cardapio FOREIGN KEY (id_cardapio) REFERENCES cardapio (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ingredientes que cada pedido consumiu (devolvidos ao estoque se ele for cancelado).
CREATE TABLE pedido_estoque (
    numero_do_pedido INT NOT NULL,
    id_ingrediente   INT NOT NULL,
    quantidade       INT NOT NULL,
    PRIMARY KEY (numero_do_pedido, id_ingrediente),
    CONSTRAINT fk_consumo_pedido FOREIGN KEY (numero_do_pedido) REFERENCES pedido (numero_do_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_consumo_ingrediente FOREIGN KEY (id_ingrediente) REFERENCES estoque (id_ingrediente) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE pagamento (
    id_pagamento       INT AUTO_INCREMENT PRIMARY KEY,
    data_hora          DATETIME      NOT NULL,
    forma_de_pagamento VARCHAR(20)   NOT NULL,
    valor              DECIMAL(10,2) NOT NULL,
    numero_do_pedido   INT           NOT NULL,
    id_cliente         INT           DEFAULT NULL,
    CONSTRAINT fk_pagamento_pedido FOREIGN KEY (numero_do_pedido) REFERENCES pedido (numero_do_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_pagamento_cliente FOREIGN KEY (id_cliente) REFERENCES cliente (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
